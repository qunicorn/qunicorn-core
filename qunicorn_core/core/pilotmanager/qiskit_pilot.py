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
import os
from typing import List

from qiskit import QuantumCircuit, transpile
from qiskit.primitives import SamplerResult, EstimatorResult
from qiskit.providers import BackendV1
from qiskit.quantum_info import SparsePauliOp
from qiskit.result import QuasiDistribution
from qiskit_ibm_provider import IBMProvider
from qiskit_ibm_provider.api.exceptions import RequestsApiError
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler, Estimator

from qunicorn_core.api.api_models import JobCoreDto
from qunicorn_core.core.pilotmanager.base_pilot import Pilot
from qunicorn_core.db.database_services import job_db_service
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.static.enums.job_state import JobState


class QiskitPilot(Pilot):
    """The Qiskit Pilot"""

    IBMQ_BACKEND = "ibmq_qasm_simulator"

    def execute(self, job_dto: JobCoreDto):
        """Execute a job on an IBM backend using the Qiskit Pilot"""

        provider = self.__get_ibm_provider_and_login(job_dto.token, job_dto.id)

        if len(job_dto.deployment.program_list) != 1:
            print(f"WARNING: Program_list of deployment is not 1, but: {job_dto.deployment.program_list}")

        backend, transpiled = self.transpile(provider, job_dto.deployment.program_list[0].quantum_circuit)

        job_db_service.update_attribute(job_dto.id, JobState.RUNNING, JobDataclass.state)

        job_from_ibm = backend.run(transpiled, shots=job_dto.shots)
        result = job_from_ibm.result()
        counts = result.get_counts()
        print("RESULTS:", result)
        job_db_service.update_finished_job(job_dto.id, str(counts))

        print(f"Run job {job_from_ibm} with id {job_dto.id} on {job_dto.executed_on.provider.name}  and get the result {counts}")

    def sample(self, job_dto: JobCoreDto):
        """Uses the Sampler to execute a job on an IBM backend using the Qiskit Pilot"""
        backend, circuit_list = self.__get_backend_circuits_and_id_for_qiskit_runtime(job_dto)
        sampler = Sampler(session=backend)
        job_from_ibm = sampler.run(circuit_list)
        results: SamplerResult = job_from_ibm.result()
        counts: list[QuasiDistribution] = results.quasi_dists
        print("RESULTS:", results)
        job_db_service.update_finished_job(job_dto.id, str(counts))
        print("SAVED JOB:", job_db_service.get_job(job_dto.id))
        print(f"Run job {job_from_ibm} with id {job_dto.id} on {job_dto.executed_on.provider.name}  and get the result {counts}")

    def estimate(self, job_dto: JobCoreDto):
        """Uses the Estimator to execute a job on an IBM backend using the Qiskit Pilot"""
        backend, circuit_list = self.__get_backend_circuits_and_id_for_qiskit_runtime(job_dto)
        estimator = Estimator(session=backend)
        job_from_ibm = estimator.run(circuit_list, observables=[SparsePauliOp("IY"), SparsePauliOp("IY")])
        results: EstimatorResult = job_from_ibm.result()
        counts = results.values
        print("RESULTS:", results)
        job_db_service.update_finished_job(job_dto.id, str(counts))

        print(f"Run job {job_from_ibm} with id {job_dto.id} on {job_dto.executed_on.provider.name}  and get the result {counts}")

    def __get_backend_circuits_and_id_for_qiskit_runtime(self, job_dto):
        """Instantiate all important configurations and updates the job_state"""
        service: QiskitRuntimeService = QiskitRuntimeService()
        self.__get_ibm_provider_and_login(job_dto.token, job_dto.id)
        job_db_service.update_attribute(job_dto.id, JobState.RUNNING, JobDataclass.state)
        circuit_list: List[QuantumCircuit] = QiskitPilot.__get_circuits_as_QuantumCircuits(job_dto)
        backend: BackendV1 = service.get_backend(self.IBMQ_BACKEND)
        return backend, circuit_list

    @staticmethod
    def __get_circuits_as_QuantumCircuits(job_dto: JobCoreDto) -> List[QuantumCircuit]:
        """Transforms the circuit string into IBM QuantumCircuit objects"""
        return [QuantumCircuit().from_qasm_str(program.quantum_circuit) for program in job_dto.deployment.program_list]

    @staticmethod
    def __get_ibm_provider_and_login(token: str, job_dto_id: int) -> IBMProvider:
        """Save account credentials and get provider"""

        # If the token is empty the token is taken from the environment variables.
        if token == "" and os.getenv("IBM_TOKEN") is not None:
            token = os.getenv("IBM_TOKEN")

        # Try to save the account. Update job_dto to job_state = Error, if it is not possible
        try:
            IBMProvider.save_account(token=token, overwrite=True)
        except RequestsApiError:
            job_db_service.update_attribute(job_dto_id, JobState.ERROR, JobDataclass.state)
            raise ValueError("The passed token is not valid.")

        # Load previously saved account credentials.
        return IBMProvider()

    def transpile(self, provider: IBMProvider, quantum_circuit_string: str):
        """Transpile job on an IBM backend, needs a device_id"""

        qasm_circ = QuantumCircuit().from_qasm_str(quantum_circuit_string)
        backend = provider.get_backend(self.IBMQ_BACKEND)
        transpiled = transpile(qasm_circ, backend=backend)

        print("Transpile a quantum circuit for a specific IBM backend")
        return backend, transpiled
