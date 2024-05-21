# Copyright 2024 University of Stuttgart
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
import json
import os
from time import sleep
from typing import Any, List, Optional, Sequence, Tuple, Union
from urllib.parse import urljoin

import requests
from qunicorn_core.api.api_models.device_dtos import DeviceDto, DeviceRequestDto
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
from qunicorn_core.util import logging

DEFAULT_QUANTUM_CIRCUIT = """OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q[1] -> c[1];
measure q[0] -> c[0];
"""

QMWARE_URL = os.environ.get("QMWARE_URL", "https://dispatcher.dev.qmware-dev.cloud/")

# TODO: read token from request body
QMWARE_API_KEY = os.environ.get("QMWARE_API_KEY", "")
QMWARE_API_KEY_ID = os.environ.get("QMWARE_API_KEY_ID", "")

AUTHORIZATION_HEADERS = {
    "X-API-KEY": QMWARE_API_KEY,
    "X-API-KEY-ID": QMWARE_API_KEY_ID,
}


class QMwarePilot(Pilot):
    """Base class for Pilots"""

    provider_name = ProviderName.QMWARE
    supported_languages = tuple([AssemblerLanguage.QASM2])

    def run(
        self, job: JobDataclass, circuits: Sequence[Tuple[QuantumProgramDataclass, Any]], token: Optional[str] = None
    ) -> Tuple[List[ResultDataclass], JobState]:
        """Run a job of type RUNNER on a backend using a Pilot"""
        if job.id is None:
            raise QunicornError("Job has no database ID and cannot be executed!")

        job_ids = []
        programs = []

        job_name = "Qunicorn request"

        for program, qasm_circuit in circuits:
            data = {
                "name": f"{job_name}",
                "maxExecutionTimeInMs": 60_000,
                "ttlAfterFinishedInMs": 1_200_000,
                "code": {"type": "qasm2", "code": qasm_circuit},
                "selectionParameters": [],
                "programParameters": [{"name": "shots", "value": str(job.shots)}],
            }

            response = requests.post(urljoin(QMWARE_URL, "/v0/requests"), json=data, headers=AUTHORIZATION_HEADERS)
            response.raise_for_status()
            result = response.json()

            if not result["jobCreated"]:
                raise ValueError(f"Job was not created. ({result['message']})")

            job_ids.append(result["id"])
            programs.append(program)

        results = []

        for job_id, program in zip(job_ids, programs):
            results.extend(QMwarePilot._get_job_results(job_id, program))

        return results, JobState.FINISHED

    @staticmethod
    def _get_job_results(job_id: str, program: QuantumProgramDataclass) -> List[ResultDataclass]:
        for _i in range(100):
            response = requests.get(urljoin(QMWARE_URL, f"/v0/jobs/{job_id}"), headers=AUTHORIZATION_HEADERS)
            response.raise_for_status()
            result = response.json()

            if result["status"] == "SUCCESS":
                break
            elif result["status"] not in ("RUNNING", "SUCCESS"):
                raise ValueError("QMware job failed")

            sleep(1)
        else:
            raise ValueError("QMware job timed out")

        measurements = json.loads(result["out"]["value"])

        if len(measurements) != 1:
            raise ValueError("currently only one register supported")

        results = measurements[0]["result"]

        counts = {element["number"]: element["hits"] for element in results}
        probabilities = {element["number"]: element["probability"] for element in results}

        return [
            ResultDataclass(
                program=program,
                data=Pilot.qubits_decimal_to_hex(counts),
                result_type=ResultType.COUNTS,
                meta={},  # TODO: save more metadata
            ),
            ResultDataclass(
                program=program,
                data=Pilot.qubits_decimal_to_hex(probabilities),
                result_type=ResultType.PROBABILITIES,
                meta={},  # TODO: save more metadata
            ),
        ]

    def execute_provider_specific(
        self, job: JobDataclass, circuits: Sequence[Tuple[QuantumProgramDataclass, Any]], token: Optional[str] = None
    ) -> Tuple[List[ResultDataclass], JobState]:
        """Execute a job of a provider specific type on a backend using a Pilot"""
        if job.id is None:
            raise QunicornError("Job has no database ID and cannot be executed!")

        error = QunicornError("No valid Job Type specified")
        job.save_error(error)

        raise error

    def get_standard_provider(self) -> ProviderDataclass:
        """Create the standard ProviderDataclass Object for the pilot and return it"""
        found_provider = ProviderDataclass.get_by_name(self.provider_name)

        if not found_provider:
            found_provider = ProviderDataclass(with_token=True, name=self.provider_name)
            found_provider.supported_languages = list(self.supported_languages)
            found_provider.save()  # make sure that the provider will be committed to DB

        return found_provider

    def get_standard_job_with_deployment(self, device: DeviceDataclass) -> JobDataclass:
        """Create the standard ProviderDataclass Object for the pilot and return it"""
        return self.create_default_job_with_circuit_and_device(device, DEFAULT_QUANTUM_CIRCUIT)

    def save_devices_from_provider(self, device_request: DeviceRequestDto):
        """Access the devices from the cloud service of the provider, to update the current device list of qunicorn"""
        raise QunicornError(
            "The QMware pilot cannot fetch devices because the QMware API doesn't have the concept of devices."
        )

    def is_device_available(self, device: Union[DeviceDataclass, DeviceDto], token: Optional[str]) -> bool:
        """Check if a device is available for a user"""
        response = requests.get(urljoin(QMWARE_URL, "/health"))

        if response.status_code != 200:
            return False

        content = response.json()

        return content["status"] == "UP"

    def get_device_data_from_provider(self, device: Union[DeviceDataclass, DeviceDto], token: Optional[str]) -> dict:
        """Get device data for a specific device from the provider"""
        raise QunicornError(
            "The QMware pilot cannot fetch devices because the QMware API doesn't have the concept of devices."
        )

    def cancel_provider_specific(self, job: JobDataclass, token: Optional[str] = None):
        """Cancel execution of a job at the corresponding backend"""
        logging.warn(
            f"Cancel job with id {job.id} on {job.executed_on.provider.name} failed."
            f"Canceling while in execution not supported for QMware Jobs"
        )
        raise QunicornError("Canceling not supported on QMware devices")
