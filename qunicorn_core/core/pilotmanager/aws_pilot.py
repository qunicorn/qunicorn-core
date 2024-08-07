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
from typing import Any, List, Optional, Sequence, Tuple, Union

from flask.globals import current_app
from braket.devices import LocalSimulator
from braket.ir.openqasm import Program
from braket.tasks import GateModelQuantumTaskResult
from braket.tasks.local_quantum_task_batch import LocalQuantumTaskBatch

from qunicorn_core.api.api_models.device_dtos import DeviceDto
from qunicorn_core.core.pilotmanager.base_pilot import Pilot
from qunicorn_core.db.models.device import DeviceDataclass
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.db.models.provider import ProviderDataclass
from qunicorn_core.db.models.quantum_program import QuantumProgramDataclass
from qunicorn_core.db.models.result import ResultDataclass
from qunicorn_core.static.enums.assembler_languages import AssemblerLanguage
from qunicorn_core.static.enums.job_state import JobState
from qunicorn_core.static.enums.provider_name import ProviderName
from qunicorn_core.static.enums.result_type import ResultType
from qunicorn_core.static.qunicorn_exception import QunicornError


class AWSPilot(Pilot):
    """The AWS Pilot"""

    provider_name = ProviderName.AWS.value
    supported_languages = tuple([AssemblerLanguage.BRAKET.value])

    def run(
        self, job: JobDataclass, circuits: Sequence[Tuple[QuantumProgramDataclass, Any]], token: Optional[str] = None
    ) -> JobState:
        """Execute the job on a local simulator and saves results in the database"""
        if job.id is None:
            raise QunicornError("Job has no database ID and cannot be executed!")
        device = job.executed_on
        if device and not device.is_local:
            raise QunicornError("Device not found, device needs to be local for AWS")

        # Since QASM is stored as a string, it needs to be converted to a QASM program before execution
        programs = [p for p, _ in circuits]
        # FIXME: support circuits where not all qubits have gates
        preprocessed_circuits = [(Program(source=c) if isinstance(c, str) else c) for _, c in circuits]

        quantum_tasks: LocalQuantumTaskBatch = LocalSimulator().run_batch(preprocessed_circuits, shots=job.shots)

        results, job_state = AWSPilot.__map_aws_results_to_dataclass(quantum_tasks.results(), programs, job)
        job.save_results(results)

        return job_state

    def execute_provider_specific(
        self, job: JobDataclass, circuits: Sequence[Tuple[QuantumProgramDataclass, Any]], token: Optional[str] = None
    ) -> JobState:
        """Execute a job of a provider specific type on a backend using a pilot"""
        if job.id is None:
            raise QunicornError("Job has no database ID and cannot be executed!")
        raise QunicornError("No valid Job Type specified")

    def cancel_provider_specific(self, job_dto):
        current_app.logger.warn(
            f"Cancel job with id {job_dto.id} on {job_dto.executed_on.provider.name} failed."
            f"Canceling while in execution not supported for AWS Jobs"
        )
        raise QunicornError("Canceling not supported on AWS devices")

    @staticmethod
    def __map_aws_results_to_dataclass(
        aws_results: list[GateModelQuantumTaskResult], programs: Sequence[QuantumProgramDataclass], job: JobDataclass
    ) -> Tuple[List[ResultDataclass], JobState]:
        """Map the results from the aws simulator to a result dataclass object"""
        results = []
        contains_errors = False

        for i, result in enumerate(aws_results):
            metadata = result.additional_metadata.dict()
            metadata["format"] = "hex"

            most_common_bitstring: str = result.measurement_counts.most_common(1)[0][0]
            metadata["registers"] = [
                {"name": "", "size": len(most_common_bitstring)}
            ]  # FIXME: support multiple registers

            try:
                results.append(
                    ResultDataclass(
                        data=Pilot.qubit_binary_string_to_hex(result.measurement_counts, reverse_qubit_order=True),
                        job=job,
                        program=programs[i],
                        meta=metadata,
                        result_type=ResultType.COUNTS,
                    )
                )
                results.append(
                    ResultDataclass(
                        data=Pilot.qubit_binary_string_to_hex(
                            result.measurement_probabilities, reverse_qubit_order=True
                        ),
                        job=job,
                        program=programs[i],
                        meta=metadata,
                        result_type=ResultType.PROBABILITIES,
                    )
                )

            except QunicornError as err:
                exception_message: str = str(err)
                stack_trace: str = "".join(traceback.format_exception(err))
                results.append(
                    ResultDataclass(
                        result_type=ResultType.ERROR.value,
                        job=job,
                        program=programs[i],
                        data={"exception_message": exception_message},
                        meta={"stack_trace": stack_trace},
                    )
                )
                contains_errors = True
        return results, JobState.ERROR if contains_errors else JobState.FINISHED

    def get_standard_job_with_deployment(self, device: DeviceDataclass) -> JobDataclass:
        return self.create_default_job_with_circuit_and_device(device, "Circuit().h(0).cnot(0, 1)")

    def save_devices_from_provider(self, token: Optional[str]):
        raise QunicornError("AWS Pilot cannot fetch Devices from AWS API, because there is no Cloud Access.")

    def get_standard_provider(self) -> ProviderDataclass:
        found_provider = ProviderDataclass.get_by_name(self.provider_name)
        if not found_provider:
            found_provider = ProviderDataclass(
                with_token=False,
                name=self.provider_name,
            )
            found_provider.supported_languages = list(self.supported_languages)
            found_provider.save()
        return found_provider

    def is_device_available(self, device: Union[DeviceDataclass, DeviceDto], token: Optional[str]) -> bool:
        current_app.logger.info("AWS local simulator is always available")
        return True
