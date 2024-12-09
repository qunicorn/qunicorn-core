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
from typing import Optional, Sequence, Union

from flask.globals import current_app
from pyquil.api import get_qc

from qunicorn_core.api.api_models import DeviceDto
from qunicorn_core.core.pilotmanager.base_pilot import Pilot, PilotJob, PilotJobResult
from qunicorn_core.db.db import DB
from qunicorn_core.db.models.device import DeviceDataclass
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.db.models.provider import ProviderDataclass
from qunicorn_core.static.enums.assembler_languages import AssemblerLanguage
from qunicorn_core.static.enums.provider_name import ProviderName
from qunicorn_core.static.enums.result_type import ResultType
from qunicorn_core.static.qunicorn_exception import QunicornError
from qunicorn_core.util import utils

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

    def run(self, jobs: Sequence[PilotJob], token: Optional[str] = None):
        """Execute the job on a local simulator and saves results in the database"""
        if utils.is_running_in_docker():
            raise QunicornError(
                "Rigetti Pilot can not be executed in Docker, check the documentation on how to run qunicorn locally to execute jobs on the Rigetti Pilot",  # noqa: E501
                HTTPStatus.NOT_IMPLEMENTED,
            )
        if any(not j.job.executed_on or not j.job.executed_on.is_local for j in jobs):
            raise QunicornError("Device need to be local for RIGETTI")

        for job in jobs:
            job.circuit.wrap_in_numshots_loop(job.job.shots)
            qvm = get_qc(job.job.executed_on.name)
            qvm_result = qvm.run(qvm.compile(job.circuit)).get_register_map().get("ro")
            result_dict = RigettiPilot.result_to_dict(qvm_result)
            result_dict = RigettiPilot.qubit_binary_string_to_hex(
                result_dict, reverse_qubit_order=True
            )  # FIXME: test qubit order with qasm testsuite!
            probabilities_dict = utils.calculate_probabilities(result_dict)

            pilot_results = [
                PilotJobResult(
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
                ),
                PilotJobResult(
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
                ),
            ]
            self.save_results(job, pilot_results)

        DB.session.commit()

    @staticmethod
    def result_to_dict(results: Sequence[Sequence[int]]) -> dict:
        """Converts the result of the qvm to a dictionary"""
        results_as_strings = ("".join(map(str, row)) for row in results)
        result_counter = Counter(results_as_strings)
        return dict(result_counter)

    def execute_provider_specific(self, jobs: Sequence[PilotJob], job_type: str, token: Optional[str] = None):
        """Execute a job of a provider specific type on a backend using a Pilot"""
        raise QunicornError("No valid Job Type specified")

    def cancel_provider_specific(self, job: JobDataclass, token: Optional[str] = None):
        raise QunicornError("Canceling not implemented for rigetti pilot yet")

    def get_standard_job_with_deployment(self, device: DeviceDataclass) -> JobDataclass:
        return self.create_default_job_with_circuit_and_device(
            device, DEFAULT_QUANTUM_CIRCUIT_1, assembler_language="QUIL-PYTHON"
        )

    def save_devices_from_provider(self, token: Optional[str]):
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
        current_app.logger.info("Rigetti local simulator is always available")
        return True
