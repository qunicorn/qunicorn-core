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

"""Test class to test the functionality of the sampler"""

from qunicorn_core.api.api_models import JobRequestDto, SimpleJobDto
from qunicorn_core.core import job_service
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.db.models.result import ResultDataclass
from qunicorn_core.static.enums.assembler_languages import AssemblerLanguage
from qunicorn_core.static.enums.job_type import JobType
from qunicorn_core.static.enums.provider_name import ProviderName
from qunicorn_core.static.enums.result_type import ResultType
from tests import test_utils
from tests.conftest import set_up_env
from tests.test_utils import (
    IS_ASYNCHRONOUS,
    PROBABILITY_1,
    PROBABILITY_TOLERANCE,
    BIT_3,
    BIT_0,
    IBM_LOCAL_SIMULATOR,
)


def test_create_and_run_estimator():
    create_and_run_estimator_with_device(IBM_LOCAL_SIMULATOR)


def create_and_run_estimator_with_device(device_name: str):
    """Tests the create and run job method for synchronous execution of a sampler"""

    app = set_up_env()
    job_request_dto: JobRequestDto = test_utils.get_test_job(ProviderName.IBM)
    job_request_dto.type = JobType.ESTIMATOR
    job_request_dto.device_name = device_name

    # WHEN: create_and_run executed synchronous
    with app.app_context():
        test_utils.save_deployment_and_add_id_to_job(job_request_dto, [AssemblerLanguage.QISKIT])
        return_dto: SimpleJobDto = job_service.create_and_run_job(job_request_dto, IS_ASYNCHRONOUS)

    # THEN: Check if the correct job with its result is saved in the db
    with app.app_context():
        test_utils.check_simple_job_dto(return_dto)
        job: JobDataclass = JobDataclass.get_by_id_or_404(return_dto.id)
        test_utils.check_if_job_finished(job)
        check_if_job_estimate_result_correct(job)


def check_if_job_estimate_result_correct(job: JobDataclass):
    test_utils.check_job_data(job)

    assert len(job.results) == 2

    for i in range(len(job.results)):
        result: ResultDataclass = job.results[i]
        assert "observer" in result.meta
        assert result.result_type == ResultType.VALUE_AND_VARIANCE
        value: float = float(result.data["value"])
        variance: float = float(result.data["variance"])

        # TODO: improve asserts
        assert -1.0 < value < 1.0
        assert -1.0 < variance < 1.0
