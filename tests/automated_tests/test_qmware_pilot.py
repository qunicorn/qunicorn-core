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

"""test in-request execution for aws"""

import pytest

from celery.result import AsyncResult
from requests import Response
from unittest.mock import patch, MagicMock, Mock

from tests.conftest import set_up_env

from qunicorn_core.core import job_service
from qunicorn_core.db.models.deployment import DeploymentDataclass
from qunicorn_core.db.models.quantum_program import QuantumProgramDataclass
from qunicorn_core.api.api_models.job_dtos import SimpleJobDto, JobRequestDto
from qunicorn_core.static.enums.job_type import JobType
from qunicorn_core.core.pilotmanager.qmware_pilot import QMwarePilot


_QMWARE_CIRCUIT = """
"""

_QMWARE_RESPONSE = {"status": "ERROR", "value": "UNKNOWN"}


@pytest.mark.celery(tasks_always_eager=True)
@patch("qunicorn_core.core.pilotmanager.qmware_pilot.requests.get")
@patch("qunicorn_core.core.pilotmanager.qmware_pilot.requests.post")
@patch("qunicorn_core.core.pilotmanager.qmware_pilot.watch_qmware_results")
def test_aws_local_simulator_braket_job_results(watch_task: MagicMock, post_job: MagicMock, get_job: MagicMock):
    app = set_up_env()

    signature = Mock()
    signature.delay.return_value = AsyncResult(id="mock-task-id")
    watch_task.s.return_value = signature

    post_response = Mock(Response)
    post_response.json.return_value = {"id": 12345, "jobCreated": True}
    post_job.return_value = post_response

    get_response = Mock(Response)
    get_response.json.return_value = _QMWARE_RESPONSE
    get_job.return_value = get_response

    with app.app_context():
        deployment = DeploymentDataclass(
            "QMWare test",
            programs=[QuantumProgramDataclass(quantum_circuit=_QMWARE_CIRCUIT, assembler_language="QASM2")],
        )
        deployment.save(commit=True)

        return_dto: SimpleJobDto = job_service.create_and_run_job(
            JobRequestDto(
                "QMWare test job",
                provider_name="QMWARE",
                device_name="dev",
                shots=1024,
                token="",
                type=JobType.RUNNER,
                deployment_id=deployment.id,
            )
        )

        watch_task.s.assert_called_once()
        signature.delay.assert_called_once()

        QMwarePilot._get_job_results(return_dto.id)

        assert return_dto  # FIXME

    post_response.raise_for_status.assert_called_once()
    post_response.json.assert_called_once()
    post_job.assert_called_once()
    get_response.raise_for_status.assert_called_once()
    get_response.json.assert_called_once()
    get_job.assert_called_once()
