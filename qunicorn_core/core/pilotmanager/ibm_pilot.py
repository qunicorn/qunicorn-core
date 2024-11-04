# Copyright 2023 University of Stuttgart
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import traceback
from http import HTTPStatus
from os import environ
from itertools import groupby
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union, Dict

import numpy as np
from flask.globals import current_app
import qiskit_aer
from qiskit import transpile, QuantumCircuit, QiskitError
from qiskit.primitives import PrimitiveResult, PubResult
from qiskit.providers import BackendV2, QiskitBackendNotFoundError
from qiskit.quantum_info import SparsePauliOp
from qiskit.result import Result
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import (
    EstimatorV2,
    IBMRuntimeError,
    QiskitRuntimeService,
    RuntimeJob,
    Sampler,
    SamplerOptions,
    RuntimeJobV2,
    EstimatorOptions,
)

from qunicorn_core.api.api_models import DeviceDto
from qunicorn_core.core.pilotmanager.base_pilot import Pilot, PilotJob, PilotJobResult
from qunicorn_core.db.db import DB
from qunicorn_core.db.models.device import DeviceDataclass
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.db.models.provider import ProviderDataclass
from qunicorn_core.db.models.result import ResultDataclass
from qunicorn_core.db.models.job_state import TransientJobStateDataclass
from qunicorn_core.static.enums.assembler_languages import AssemblerLanguage
from qunicorn_core.static.enums.error_mitigation import ErrorMitigationMethod
from qunicorn_core.static.enums.job_state import JobState
from qunicorn_core.static.enums.job_type import JobType
from qunicorn_core.static.enums.provider_name import ProviderName
from qunicorn_core.static.enums.result_type import ResultType
from qunicorn_core.static.qunicorn_exception import QunicornError
from qunicorn_core.util import utils


class IBMPilot(Pilot):
    """The IBM Pilot"""

    provider_name = ProviderName.IBM.value
    supported_languages = tuple([AssemblerLanguage.QISKIT.value])

    def execute_provider_specific(self, jobs: Sequence[PilotJob], job_type: str, token: Optional[str] = None):
        """Execute a job of a provider specific type on a backend using a Pilot"""

        if job_type == JobType.ESTIMATOR.value:
            self.__estimate(jobs, token=token)
        elif job_type == JobType.SAMPLER.value:
            self.__sample(jobs, token=token)
        elif job_type == JobType.IBM_RUNNER.value:
            self.__run_ibm_program(jobs, token=token)
        elif job_type == JobType.IBM_UPLOAD.value:
            self.__upload_ibm_program(jobs, token=token)
        else:
            raise QunicornError("No valid Job Type specified")

    def run(self, jobs: Sequence[PilotJob], token: Optional[str] = None):
        """Execute a job local using aer simulator or a real backend"""
        batched_jobs = [(db_job, list(pilot_jobs)) for db_job, pilot_jobs in groupby(jobs, lambda j: j.job)]

        for db_job, pilot_jobs in batched_jobs:
            device = db_job.executed_on
            if device is None:
                db_job.save_error(QunicornError("The job does not have any device associated!"))
                continue  # one job failing should not affect other jobs

            backend: BackendV2
            if device.is_local:
                backend = qiskit_aer.Aer.get_backend("aer_simulator")
            else:
                provider = self.__get_provider_login_and_update_job(token, db_job)
                backend = provider.backend(device.name)

            pilot_jobs = list(pilot_jobs)

            backend_specific_circuits = transpile([j.circuit for j in pilot_jobs], backend)
            qiskit_job = backend.run(backend_specific_circuits, shots=db_job.shots)

            job_state: Optional[TransientJobStateDataclass] = None

            for state in db_job._transient:
                if state.program is not None and isinstance(state.data, dict):
                    if state.data.get("type") == "IBM":
                        job_state = state
                        break
            else:
                job_state = TransientJobStateDataclass(db_job, data={"type": "IBM"})

            provider_specific_ids = job_state.data.get("provider_ids", [])
            provider_specific_ids.append(qiskit_job.job_id())
            job_state.data = dict(job_state.data) | {"provider_ids": provider_specific_ids}
            job_state.save()

            db_job.state = JobState.RUNNING.value
            db_job.save(commit=True)

            result = qiskit_job.result()
            mapped_results: list[Sequence[PilotJobResult]] = IBMPilot.__map_runner_results(
                result, backend_specific_circuits
            )

            for pilot_results, pilot_job in zip(mapped_results, pilot_jobs):
                self.save_results(pilot_job, pilot_results)
            DB.session.commit()

    def cancel_provider_specific(self, job: JobDataclass, token: Optional[str] = None):
        """Cancel a job on an IBM backend using the IBM Pilot"""
        qiskit_job = self.__get_qiskit_job_from_qiskit_runtime(job, token=token)
        qiskit_job.cancel()
        job.state = JobState.CANCELED.value
        job.save(commit=True)
        current_app.logger.info(f"Cancel job with id {job.id} on {job.executed_on.provider.name} successful.")

    def __sample(self, jobs: Sequence[PilotJob], token: Optional[str] = None) -> Tuple[List[ResultDataclass], JobState]:
        """Uses the Sampler to execute a job on an IBM backend using the IBM Pilot"""
        batched_jobs = [(db_job, list(pilot_jobs)) for db_job, pilot_jobs in groupby(jobs, lambda j: j.job)]
        db_job: JobDataclass

        for db_job, pilot_jobs in batched_jobs:
            options = SamplerOptions()

            if db_job.error_mitigation == ErrorMitigationMethod.none.value:
                pass
            elif db_job.error_mitigation == ErrorMitigationMethod.dynamical_decoupling.value:
                options.dynamical_decoupling.enable = True
            elif db_job.error_mitigation == ErrorMitigationMethod.pauli_twirling.value:
                options.enable_gates = True
            else:
                raise QunicornError(f"Error mitigation method {db_job.error_mitigation} not supported by IBM sampler.")

            if db_job.executed_on.is_local:
                backend = AerSimulator()
            else:
                backend = self.__get_qiskit_runtime_backend(db_job, token=token)

            sampler = Sampler(backend, options=options)

            job_from_ibm: RuntimeJobV2 = sampler.run([j.circuit for j in pilot_jobs])
            ibm_result: PrimitiveResult = job_from_ibm.result()
            mapped_results = IBMPilot._map_sampler_results(ibm_result)

            for pilot_results, pilot_job in zip(mapped_results, pilot_jobs):
                self.save_results(pilot_job, pilot_results)
            DB.session.commit()

    def __estimate(self, jobs: Sequence[PilotJob], token: Optional[str] = None):  # noqa: C901
        """Uses the Estimator to execute a job on an IBM backend using the IBM Pilot"""
        batched_jobs = [(db_job, list(pilot_jobs)) for db_job, pilot_jobs in groupby(jobs, lambda j: j.job)]

        for db_job, pilot_jobs in batched_jobs:
            observables = [SparsePauliOp("Y" * job.circuit.num_qubits) for job in pilot_jobs]
            options = EstimatorOptions()

            if db_job.error_mitigation == ErrorMitigationMethod.none.value:
                pass
            elif db_job.error_mitigation == ErrorMitigationMethod.dynamical_decoupling.value:
                options.dynamical_decoupling.enable = True
            elif db_job.error_mitigation == ErrorMitigationMethod.pauli_twirling.value:
                options.enable_gates = True
            elif db_job.error_mitigation == ErrorMitigationMethod.twirled_readout_error_extinction:
                options.resilience.measure_mitigation = True
            elif db_job.error_mitigation == ErrorMitigationMethod.zero_noise_extrapolation:
                options.resilience.zne_mitigation = True
            elif db_job.error_mitigation == ErrorMitigationMethod.probabilistic_error_amplification:
                options.resilience.zne_mitigation = True
                options.resilience.zne.amplifier = "pea"
            elif db_job.error_mitigation == ErrorMitigationMethod.probabilistic_error_cancellation:
                options.resilience.pec_mitigation = True
            else:
                raise QunicornError(
                    f"Error mitigation method {db_job.error_mitigation} not supported by IBM estimator."
                )

            if db_job.executed_on.is_local:
                backend = AerSimulator()
            else:
                backend = self.__get_qiskit_runtime_backend(db_job, token=token)

            estimator = EstimatorV2(backend, options=options)
            circuits = [j.circuit for j in pilot_jobs]

            job_from_ibm = estimator.run(list(zip(circuits, observables)))
            ibm_result: PrimitiveResult = job_from_ibm.result()
            mapped_results = IBMPilot._map_estimator_results(ibm_result, observables)

            for pilot_results, pilot_job in zip(mapped_results, pilot_jobs):
                self.save_results(pilot_job, pilot_results)
            DB.session.commit()

    def __get_qiskit_runtime_backend(self, job: JobDataclass, token: Optional[str]) -> BackendV2:
        """Instantiate all important configurations and updates the job_state"""

        # If the token is empty the token is taken from the environment variables.
        if not token and (t := environ.get("IBM_TOKEN")):
            token = t

        self.__get_provider_login_and_update_job(token, job)
        return QiskitRuntimeService().backend(job.executed_on.name)

    def __get_qiskit_job_from_qiskit_runtime(self, job: JobDataclass, token: Optional[str]) -> RuntimeJob:
        """Returns the job of the provider specific ID created on the given account"""

        # If the token is empty the token is taken from the environment variables.
        if not token and (t := environ.get("IBM_TOKEN")):
            token = t

        self.__get_provider_login_and_update_job(token, job.id)
        service: QiskitRuntimeService = QiskitRuntimeService()
        return service.job(job.provider_specific_id)  # FIXME use ids from transient state!

    @staticmethod
    def get_ibm_provider_and_login(token: Optional[str]) -> QiskitRuntimeService:
        """Save account credentials and get provider"""

        # If the token is empty the token is taken from the environment variables.
        if not token and (t := environ.get("IBM_TOKEN")):
            token = t

        # Try to save the account. Update job_dto to job_state = Error, if it is not possible
        # FIXME test and use job specific name for saving credentials??
        file_path = Path(current_app.instance_path) / "qiskit_accounts"
        file_path.mkdir(exist_ok=True, parents=True)
        file_path /= "ibm_account.json"

        QiskitRuntimeService.save_account(
            channel="ibm_quantum", token=token, overwrite=True, name="TODO", filename=str(file_path)
        )

        return QiskitRuntimeService(channel="ibm_quantum", name="TODO", filename=str(file_path))  # FIXME change name

    @staticmethod
    def __get_provider_login_and_update_job(token: str, job: JobDataclass) -> QiskitRuntimeService:
        """Save account credentials, get provider and update job_dto to job_state = Error, if it is not possible"""

        try:
            return IBMPilot.get_ibm_provider_and_login(token)
        except Exception as exception:
            job.save_error(exception)
            raise QunicornError(type(exception).__name__ + ": " + str(exception.args), HTTPStatus.UNAUTHORIZED)

    @staticmethod
    def __get_file_path_to_resources(file_name) -> str:
        # TODO: resources should be placed relative to the app instance folder!!! (or in the database)
        working_directory_path = Path(".").resolve()
        file_path = working_directory_path / "resources" / "upload_files" / file_name
        return str(file_path)

    def __upload_ibm_program(self, jobs: Sequence[PilotJob], token: Optional[str]):
        """EXPERIMENTAL -- Upload and then run a quantum program on the QiskitRuntimeService"""
        for job in jobs:
            self.check_if_env_variable_true_for_experimental(job.job)

            service = self.__get_runtime_service(job.job, token=token)

            # FIXME refactor: this should only upload a single program per pilot job!!!
            ibm_program_ids = []
            for program in job.job.deployment.programs:
                python_file_path = self.__get_file_path_to_resources(program.python_file_path)
                python_file_metadata_path = self.__get_file_path_to_resources(program.python_file_metadata)
                ibm_program_ids.append(service.upload_program(python_file_path, python_file_metadata_path))

            job.job.type = JobType.IBM_RUNNER.value
            job.job.save(commit=True)
            result_type: ResultType = ResultType.UPLOAD_SUCCESSFUL
            ibm_results = [PilotJobResult(data={"ibm_job_id": ibm_program_ids[0]}, meta={}, result_type=result_type)]
            print(ibm_results)
            # FIXME save results
            # FIXME set job state to ready once all programs are uploaded?

    def __run_ibm_program(self, jobs: Sequence[PilotJob], token: Optional[str]):
        """EXPERIMENTAL -- Run a program previously uploaded to the IBM Backend"""
        for job in jobs:
            self.check_if_env_variable_true_for_experimental(job.job)

            service = self.__get_runtime_service(job.job, token=token)
            options_dict: Optional[dict] = None  # job.ibm_file_options  # FIXME
            input_dict: Optional[dict] = None  # job.ibm_file_inputs  # FIXME
            ibm_job_id = job.job.results[0].data["ibm_job_id"]  # FIXME

            try:
                result: RuntimeJob = service.run(ibm_job_id, inputs=input_dict, options=options_dict).result()
            except IBMRuntimeError as exception:
                job.job.save_error(exception)
                raise QunicornError(type(exception).__name__, HTTPStatus.INTERNAL_SERVER_ERROR)

            # use assert to pacify linter for now...
            assert result  # FIXME: actually use result object
            ibm_results: list[PilotJobResult] = []  # FIXME: map result to list of ResultDataclass
            print(ibm_results)
            # FIXME save results in db

    @staticmethod
    def check_if_env_variable_true_for_experimental(job: JobDataclass):
        """EXPERIMENTAL -- Raise an error if the experimental env variable is not true and logs a warning"""

        exception_str: str = (
            "Running uploaded IBM Programs is experimental and has not been fully tested yet."
            "Set ENABLE_EXPERIMENTAL_FEATURES to True to enable this feature."
        )

        if not utils.is_experimental_feature_enabled():
            exception: Exception = QunicornError(exception_str, HTTPStatus.NOT_IMPLEMENTED)
            job.save_error(exception)
            raise exception

        current_app.logger.warn("This function is experimental and could not be fully tested yet")

    @staticmethod
    def __get_runtime_service(job: JobDataclass, token: Optional[str]) -> QiskitRuntimeService:
        # If the token is empty the token is taken from the environment variables.
        if not token and (t := environ.get("IBM_TOKEN")):
            token = t

        service = QiskitRuntimeService(token=None, channel=None, filename=None, name=None)
        service.save_account(token=token, channel="ibm_quantum", overwrite=True)
        return service

    @staticmethod
    def __map_runner_results(
        ibm_result: Result, circuits: List[QuantumCircuit] = None
    ) -> list[Sequence[PilotJobResult]]:
        results: list[Sequence[PilotJobResult]] = []

        try:
            binary_counts = ibm_result.get_counts()
        except QiskitError:
            binary_counts = [None]

        if isinstance(binary_counts, dict):
            binary_counts = [binary_counts]

        for i, result in enumerate(ibm_result.results):
            pilot_results: list[PilotJobResult] = []
            results.append(pilot_results)

            metadata = result.to_dict()
            metadata["format"] = "hex"
            classical_registers_metadata = []

            for reg in reversed(circuits[i].cregs):
                # FIXME: don't append registers that are not measured
                classical_registers_metadata.append({"name": reg.name, "size": reg.size})

            metadata["registers"] = classical_registers_metadata
            metadata.pop("data")
            metadata.pop("circuit", None)

            hex_counts = IBMPilot._binary_counts_to_hex(binary_counts[i])

            pilot_results.append(
                PilotJobResult(
                    result_type=ResultType.COUNTS,
                    data=hex_counts if hex_counts else {"": 0},
                    meta=metadata,
                )
            )

            probabilities: dict = Pilot.calculate_probabilities(hex_counts) if hex_counts else {"": 0}

            pilot_results.append(
                PilotJobResult(
                    result_type=ResultType.PROBABILITIES,
                    data=probabilities,
                    meta=metadata,
                )
            )
        return results

    @staticmethod
    def _binary_counts_to_hex(binary_counts: Dict[str, int] | None) -> Dict[str, int] | None:
        if binary_counts is None:
            return None

        hex_counts = {}

        for k, v in binary_counts.items():
            hex_registers = []

            for binary_register in k.split():
                hex_registers.append(f"0x{int(binary_register, 2):x}")

            hex_sample = " ".join(hex_registers)

            hex_counts[hex_sample] = v

        return hex_counts

    @staticmethod
    def _map_estimator_results(
        ibm_result: PrimitiveResult, observables: List[SparsePauliOp]
    ) -> list[Sequence[PilotJobResult]]:
        mapped_results: list[Sequence[PilotJobResult]] = []

        for i in range(len(ibm_result)):
            pub_result: PubResult = ibm_result[i]
            expectation_values: np.ndarray = pub_result.data["evs"]
            standard_deviations: np.ndarray = pub_result.data["stds"]
            variance = standard_deviations * standard_deviations

            mapped_results.append(
                [
                    PilotJobResult(
                        data={"value": str(expectation_values.item()), "variance": str(variance.item())},
                        meta={"observer": f"SparsePauliOp-{observables[i].paulis}"},
                        result_type=ResultType.VALUE_AND_VARIANCE,
                    )
                ]
            )

        return mapped_results

    @staticmethod
    def _map_sampler_results(ibm_result: PrimitiveResult) -> list[Sequence[PilotJobResult]]:
        mapped_results: list[Sequence[PilotJobResult]] = []

        for i in range(len(ibm_result)):
            pilot_results: list[PilotJobResult] = []
            try:
                pilot_results.append(
                    PilotJobResult(
                        data=Pilot.qubit_binary_string_to_hex(ibm_result[i].data["c"].get_counts()),
                        meta={},
                        result_type=ResultType.COUNTS,
                    )
                )
            except QunicornError as err:
                exception_message: str = str(err)
                stack_trace: str = "".join(traceback.format_exception(err))
                pilot_results.append(
                    PilotJobResult(
                        result_type=ResultType.ERROR,
                        data={"exception_message": exception_message},
                        meta={"stack_trace": stack_trace},
                    )
                )

            mapped_results.append(pilot_results)

        return mapped_results

    def get_standard_provider(self) -> ProviderDataclass:
        found_provider = ProviderDataclass.get_by_name(self.provider_name)
        if not found_provider:
            found_provider = ProviderDataclass(with_token=True, name=self.provider_name)
            found_provider.supported_languages = list(self.supported_languages)
            found_provider.save()  # make sure that the provider will be committed to DB
        return found_provider

    def get_standard_job_with_deployment(self, device: DeviceDataclass) -> JobDataclass:
        circuit: str = (
            "circuit = QuantumCircuit(2, 2);circuit.h(0); circuit.cx(0, 1);circuit.measure(0, 0);circuit.measure(1, 1)"
        )
        return self.create_default_job_with_circuit_and_device(device, circuit, assembler_language="QISKIT-PYTHON")

    def save_devices_from_provider(self, token: Optional[str]):
        ibm_provider: QiskitRuntimeService = IBMPilot.get_ibm_provider_and_login(token)
        all_devices = ibm_provider.backends()

        provider: Optional[ProviderDataclass] = self.get_standard_provider()

        # First save all devices from the cloud service
        for ibm_device in all_devices:
            found_device = DeviceDataclass.get_by_name(ibm_device.name, provider)
            if not found_device:
                found_device = DeviceDataclass(
                    name=ibm_device.name,
                    num_qubits=-1 if ibm_device.name.__contains__("stabilizer") else ibm_device.num_qubits,
                    is_simulator=ibm_device.name.__contains__("simulator"),
                    is_local=False,
                    provider=provider,
                )
            else:
                found_device.num_qubits = -1 if ibm_device.name.__contains__("stabilizer") else ibm_device.num_qubits
                found_device.is_simulator = ibm_device.name.__contains__("simulator")
                found_device.is_local = False
            found_device.save()

        found_aer_device = DeviceDataclass.get_by_name("aer_simulator", provider)
        if not found_aer_device:
            # Then add the local simulator
            found_aer_device = DeviceDataclass(
                name="aer_simulator",
                num_qubits=-1,
                is_simulator=True,
                is_local=True,
                provider=provider,
            )
        else:
            found_aer_device.num_qubits = -1
            found_aer_device.is_simulator = True
            found_aer_device.is_local = True
        found_aer_device.save(commit=True)

    def is_device_available(self, device: Union[DeviceDataclass, DeviceDto], token: Optional[str]) -> bool:
        ibm_provider: QiskitRuntimeService = IBMPilot.get_ibm_provider_and_login(token)
        if device.is_simulator:
            return True
        try:
            ibm_provider.get_backend(device.name)
            return True
        except QiskitBackendNotFoundError:
            return False

    def get_device_data_from_provider(self, device: Union[DeviceDataclass, DeviceDto], token: Optional[str]) -> dict:
        ibm_provider: QiskitRuntimeService = IBMPilot.get_ibm_provider_and_login(token)
        backend = ibm_provider.get_backend(device.name)
        config_dict: dict = vars(backend.configuration())
        # Remove some not serializable fields
        config_dict["u_channel_lo"] = None
        config_dict["_qubit_channel_map"] = None
        config_dict["_channel_qubit_map"] = None
        config_dict["_control_channels"] = None
        config_dict["gates"] = None
        return config_dict
