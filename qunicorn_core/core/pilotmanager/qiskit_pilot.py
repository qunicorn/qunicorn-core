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
from qiskit.primitives import SamplerResult
from qiskit_ibm_provider import IBMProvider
from qiskit_ibm_provider.api.exceptions import RequestsApiError
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler

from qunicorn_core.api.api_models import JobCoreDto, QuantumProgramDto
from qunicorn_core.core.pilotmanager.base_pilot import Pilot
from qunicorn_core.db.database_services import job_db_service
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.static.enums.job_state import JobState


class QiskitPilot(Pilot):
    """The Qiskit Pilot"""

    IBMQ_BACKEND = "ibmq_qasm_simulator"

    def execute(self, job_dto: JobCoreDto):
        """Execute a job on an IBM backend using the Qiskit Pilot"""

        try:
            provider = self.__get_ibm_provider_and_login(job_dto.token)
        except RequestsApiError:
            job_db_service.update_attribute(job_dto.id, JobState.ERROR, JobDataclass.state)
            raise ValueError("The passed token is not valid.")

        backend, transpiled = self.transpile(provider, job_dto.deployment.quantum_program.quantum_circuit)
        job_id = job_dto.id

        job_db_service.update_attribute(job_id, JobState.RUNNING, JobDataclass.state)

        job_from_ibm = backend.run(transpiled, shots=job_dto.shots)
        counts = job_from_ibm.result().get_counts()
        job_db_service.update_result_and_state(job_id, JobState.FINISHED, str(counts))

        print(f"Job with id {job_id} complete")
        print(f"Executing job {job_from_ibm} " 
              f"on {job_dto.executed_on.provider.name} with the Qiskit Pilot and get the result {counts}")
        return counts

    def sample(self, job_dto: JobCoreDto):
        """Execute a job on an IBM backend using the Qiskit Pilot"""
        job_id = job_dto.id

        service = QiskitRuntimeService()
        self.__get_ibm_provider_and_login(job_dto.token)
        backend = service.get_backend(self.IBMQ_BACKEND)
        sampler = Sampler(session=backend)
        program_list: List[QuantumProgramDto] = job_dto.deployment.program_list
        circuit_list: List[QuantumCircuit] = [QuantumCircuit().from_qasm_str(program.quantum_circuit) for program in program_list]
        job_db_service.update_attribute(job_id, JobState.RUNNING, JobDataclass.state)
        job_from_ibm = sampler.run(circuit_list)
        counts: SamplerResult = job_from_ibm.result().quasi_dists
        job_db_service.update_result_and_state(job_id, JobState.FINISHED, str(counts))

        print(f"Job with id {job_id} complete")
        print(f"Sampling job {job_from_ibm} "
              f"on {job_dto.executed_on.provider.name} with the Qiskit Pilot and get the result {counts}")
        return counts

    @staticmethod
    def __get_ibm_provider_and_login(token: str) -> IBMProvider:
        """Save account credentials and get provider"""

        # Save account credentials.
        # You can get you token in your account settings of the front page
        if token == "" and os.getenv("IBM_TOKEN") is not None:
            token = os.getenv("IBM_TOKEN")
        IBMProvider.save_account(token=token, overwrite=True)

        # Load previously saved account credentials.
        return IBMProvider()

    def transpile(self, provider: IBMProvider, quantum_circuit_string: str):
        """Transpile job on an IBM backend, needs a device_id"""

        qasm_circ = QuantumCircuit().from_qasm_str(quantum_circuit_string)
        backend = provider.get_backend(self.IBMQ_BACKEND)
        transpiled = transpile(qasm_circ, backend=backend)

        print("Transpile a quantum circuit for a specific IBM backend")
        return backend, transpiled
