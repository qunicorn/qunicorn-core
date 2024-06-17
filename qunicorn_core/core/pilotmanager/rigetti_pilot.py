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

from collections import Counter
from http import HTTPStatus
from typing import Any, Optional, Sequence, Tuple, Union

from pyquil.api import get_qc

from qunicorn_core.api.api_models import DeviceDto
from qunicorn_core.core.pilotmanager.base_pilot import Pilot
from qunicorn_core.db.models.device import DeviceDataclass
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.db.models.provider import ProviderDataclass
from qunicorn_core.db.models.quantum_program import QuantumProgramDataclass
from qunicorn_core.db.models.result import ResultDataclass
from qunicorn_core.static.enums.assembler_languages import AssemblerLanguage
from qunicorn_core.static.enums.provider_name import ProviderName
from qunicorn_core.static.enums.result_type import ResultType
from qunicorn_core.static.qunicorn_exception import QunicornError
from qunicorn_core.util import logging, utils

DEFAULT_QUANTUM_CIRCUIT_1 = """from pyquil import Program \n
from pyquil.gates import * \n
from pyquil.quilbase import Declare\n
circuit = Program(
Declare(\"ro\", \"BIT\", 2),
H(0),
CNOT(0, 1),
MEASURE(0, (\"ro\", 0)),
MEASURE(1, (\"ro\", 1)),
)"""


class RigettiPilot(Pilot):
    """The Rigetti Pilot"""

    provider_name: str = ProviderName.RIGETTI.value

    supported_languages: list[str] = [AssemblerLanguage.QUIL.value]

    def run(
        self, job: JobDataclass, circuits: Sequence[Tuple[QuantumProgramDataclass, Any]], token: Optional[str] = None
    ) -> list[ResultDataclass]:
        """Execute the job on a local simulator and saves results in the database"""
        if utils.is_running_in_docker():
            error = QunicornError(
                "Rigetti Pilot can not be executed in Docker, check the documentation on how to run qunicorn locally to execute jobs on the Rigetti Pilot",  # noqa: E501
                HTTPStatus.NOT_IMPLEMENTED,
            )
            job.save_error(error)
            raise error
        if job.executed_on.is_local:
            results = []

            for program, circuit in circuits:
                circuit.wrap_in_numshots_loop(job.shots)
                qvm = get_qc(job.executed_on.name)
                qvm_result = qvm.run(qvm.compile(circuit)).get_register_map().get("ro")
                result_dict = RigettiPilot.result_to_dict(qvm_result)
                result_dict = RigettiPilot.qubit_binary_string_to_hex(result_dict, job.id)
                probabilities_dict = RigettiPilot.calculate_probabilities(result_dict)
                results.append(
                    ResultDataclass(
                        program=program,
                        data=result_dict,
                        result_type=ResultType.COUNTS,
                        meta={
                            "format": "hex",
                            "shots": qvm_result.shape[0],
                            "registers": {
                                "name": "default",
                                "size": qvm_result.shape[1],
                            },
                        },
                    )
                )
                results.append(
                    ResultDataclass(
                        program=program,
                        data=probabilities_dict,
                        result_type=ResultType.PROBABILITIES,
                        meta={
                            "format": "hex",
                            "shots": qvm_result.shape[0],
                            "registers": {
                                "name": "default",
                                "size": qvm_result.shape[1],
                            },
                        },
                    )
                )
            return results
        else:
            error = QunicornError("Device need to be local for RIGETTI")
            job.save_error(error)
            raise error

    @staticmethod
    def result_to_dict(results: Sequence[Sequence[int]]) -> dict:
        """Converts the result of the qvm to a dictionary"""
        results_as_strings = ("".join(map(str, row)) for row in results)
        result_counter = Counter(results_as_strings)
        return dict(result_counter)

    def execute_provider_specific(
        self, job: JobDataclass, circuits: Sequence[Tuple[QuantumProgramDataclass, Any]], token: Optional[str] = None
    ):
        """Execute a job of a provider specific type on a backend using a Pilot"""
        error = QunicornError("No valid Job Type specified")
        job.save_error(error)
        raise error

    def cancel_provider_specific(self, job: JobDataclass, token: Optional[str] = None):
        raise QunicornError("Canceling not implemented for rigetti pilot yet")

    def get_standard_job_with_deployment(self, device: DeviceDataclass) -> JobDataclass:
        return self.create_default_job_with_circuit_and_device(
            device, DEFAULT_QUANTUM_CIRCUIT_1, assembler_language="QUIL-PYTHON"
        )

    def save_devices_from_provider(self, device_request):
        raise QunicornError(
            "Rigetti Pilot cannot fetch Devices from Rigetti Computing, because there is no Cloud Access."
        )

    def get_standard_provider(self):
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
        logging.info("Rigetti local simulator is always available")
        return True
