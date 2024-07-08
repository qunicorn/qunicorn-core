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
from time import time
from typing import Any, List, Optional, Sequence, Tuple, Union, Dict
from urllib.parse import urljoin

import requests
from flask.globals import current_app
from qiskit import qasm2
from requests.exceptions import ConnectionError

from qunicorn_core.celery import CELERY
from qunicorn_core.api.api_models.device_dtos import DeviceDto
from qunicorn_core.core.pilotmanager.base_pilot import Pilot
from qunicorn_core.db.models.device import DeviceDataclass
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.db.models.job_state import TransientJobStateDataclass
from qunicorn_core.db.models.provider import ProviderDataclass
from qunicorn_core.db.models.quantum_program import QuantumProgramDataclass
from qunicorn_core.db.models.result import ResultDataclass
from qunicorn_core.static.enums.assembler_languages import AssemblerLanguage
from qunicorn_core.static.enums.job_state import JobState
from qunicorn_core.static.enums.provider_name import ProviderName
from qunicorn_core.static.enums.result_type import ResultType
from qunicorn_core.static.qunicorn_exception import QunicornError

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


class QMWAREResultsPending(Exception):
    pass


class QMwarePilot(Pilot):
    """Base class for Pilots"""

    provider_name = ProviderName.QMWARE
    supported_languages = tuple([AssemblerLanguage.QASM2])

    def run(
        self,
        qunicorn_job: JobDataclass,
        circuits: Sequence[Tuple[QuantumProgramDataclass, Any]],
        token: Optional[str] = None,
    ) -> JobState:
        """Run a job of type RUNNER on a backend using a Pilot"""
        if qunicorn_job.id is None:
            raise QunicornError("Job has no database ID and cannot be executed!")

        job_name = "Qunicorn request"

        for program, qasm_circuit in circuits:
            data = {
                "name": f"{job_name}",
                "maxExecutionTimeInMs": 60_000,
                "ttlAfterFinishedInMs": 1_200_000,
                "code": {"type": "qasm2", "code": qasm_circuit},
                "selectionParameters": [],
                "programParameters": [{"name": "shots", "value": str(qunicorn_job.shots)}],
            }

            response = requests.post(
                urljoin(QMWARE_URL, "/v0/requests"), json=data, headers=AUTHORIZATION_HEADERS, timeout=10
            )
            response.raise_for_status()

            result = response.json()

            if not result["jobCreated"]:
                raise QunicornError(f"Job was not created. ({result['message']})")

            program_state = TransientJobStateDataclass(
                job=qunicorn_job,
                program=program,
                data={
                    "id": result["id"],
                    "started_at": int(time()),
                    "X-API-KEY": QMWARE_API_KEY,
                    "X-API-KEY-ID": QMWARE_API_KEY_ID,
                    "circuit": qasm_circuit,
                },
            )
            program_state.save()

        qunicorn_job.state = JobState.RUNNING.value
        qunicorn_job.save(commit=True)  # make sure transient state is available

        watch_task = watch_qmware_results.s(job_id=qunicorn_job.id).delay()
        qunicorn_job.celery_id = watch_task.id
        qunicorn_job.save(commit=True)  # commit new celery id

        return JobState.RUNNING

    @staticmethod
    def _get_job_results(qunicorn_job_id: int) -> List[ResultDataclass] | None:  # noqa: C901
        qunicorn_job = JobDataclass.get_by_id(qunicorn_job_id)

        if qunicorn_job is None:
            raise ValueError("Unknown Qunicorn job id {qunicorn_job_id}!")

        for program_state in tuple(qunicorn_job._transient):
            if program_state.program is None:
                continue  # only process program related transient state

            job_started_at = program_state.data["started_at"]
            qmware_job_id = program_state.data["id"]
            program = program_state.program

            if job_started_at + (24 * 3600) < time():
                # time out jobs after 24 hours!
                program_state.delete()
                error = QunicornError(f"QMware job with id {qmware_job_id} timed out!")
                qunicorn_job.save_error(error, program=program)
                continue

            response = requests.get(
                urljoin(QMWARE_URL, f"/v0/jobs/{qmware_job_id}"),
                headers={
                    "X-API-KEY": program_state.data["X-API-KEY"],
                    "X-API-KEY-ID": program_state.data["X-API-KEY-ID"],
                },
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if result["status"] in ("WAITING", "PREPARING", "RUNNING"):
                raise QMWAREResultsPending()

            if result["status"] in ("ERROR", "TIMEOUT", "CANCELED"):
                program_state.delete()
                error = QunicornError(f"QMware job with id {qmware_job_id} returned status {result['status']}")
                qunicorn_job.save_error(error, program=program)

            if result["status"] != "SUCCESS":
                program_state.delete()
                error = QunicornError(f"QMware job with id {qmware_job_id} returned unknown status {result['status']}")
                qunicorn_job.save_error(error, program=program)

            measurements: List[Dict] = json.loads(result["out"]["value"])
            results: List[List[Dict[str, int]]] = [measurement["result"] for measurement in measurements]
            hex_counts = {}
            hex_probabilities = {}

            for single_result in zip(*results):
                hex_measurements = []
                hits = None
                register: Dict[str, int]

                for register in single_result:
                    hex_measurements.append(hex(register["number"]))

                    if hits is None:
                        hits = register["hits"]
                    else:
                        assert hits == register["hits"], "results have different number of hits"

                if hits is None:
                    hits = 0

                hex_measurement = " ".join(hex_measurements)
                hex_counts[hex_measurement] = hits
                hex_probabilities[hex_measurement] = hits / qunicorn_job.shots

            circuit = qasm2.loads(program_state.data["circuit"])
            register_metadata = []

            for classical_register in circuit.cregs:
                register_metadata.append(
                    {
                        "name": classical_register.name,
                        "size": classical_register.size,
                    }
                )

            ResultDataclass(
                job=qunicorn_job,
                program=program,
                data=hex_counts,
                result_type=ResultType.COUNTS,
                meta={
                    "format": "hex",
                    "shots": qunicorn_job.shots,
                    "registers": register_metadata,
                },
            ).save()
            ResultDataclass(
                program=program,
                data=hex_probabilities,
                result_type=ResultType.PROBABILITIES,
                meta={
                    "format": "hex",
                    "shots": qunicorn_job.shots,
                    "registers": register_metadata,
                },
            ).save()
            program_state.delete(commit=True)

        # all programs have results
        if qunicorn_job.state == JobState.RUNNING.value:
            # all jobs have finished without errors
            qunicorn_job.state = JobState.FINISHED

    def execute_provider_specific(
        self, job: JobDataclass, circuits: Sequence[Tuple[QuantumProgramDataclass, Any]], token: Optional[str] = None
    ) -> JobState:
        """Execute a job of a provider specific type on a backend using a Pilot"""
        if job.id is None:
            raise QunicornError("Job has no database ID and cannot be executed!")

        raise QunicornError("No valid Job Type specified")

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

    def save_devices_from_provider(self, token: Optional[str]):
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
        current_app.logger.warn(
            f"Cancel job with id {job.id} on {job.executed_on.provider.name} failed."
            f"Canceling while in execution not supported for QMware Jobs"
        )
        raise QunicornError("Canceling not supported on QMware devices")


@CELERY.task(
    ignore_result=True,
    autoretry_for=(QMWAREResultsPending, ConnectionError),
    retry_backoff=True,
    max_retries=None,
)
def watch_qmware_results(job_id: int):
    QMwarePilot._get_job_results(job_id)
