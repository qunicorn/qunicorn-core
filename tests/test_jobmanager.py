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

""""Test class to test the functionality of the job_api"""
import json
import os

from qunicorn_core.api.api_models import JobRequestDto, SimpleJobDto
from qunicorn_core.core.jobmanager.jobmanager_service import create_and_run_job
from qunicorn_core.db.database_services import job_db_service
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.static.enums.job_state import JobState
from tests.test_config import set_up_env


def test_create_and_run_sampler():
    """Tests the create and run job method for synchronous execution of a sampler"""

    app = set_up_env()
    data = get_object_from_json('job_test_data_sampler.json')
    with app.app_context():
        job_dto: JobRequestDto = JobRequestDto(**data)
        return_dto: SimpleJobDto = create_and_run_job(job_dto, False)
        assert return_dto.id == '2' and return_dto.name == 'JobName' and return_dto.job_state == JobState.RUNNING
        job: JobDataclass = job_db_service.get_job(return_dto.id)
        check_if_job_finished(job)
        print(job)
    print("create_and_run_job test ended")


def check_if_job_finished(job: JobDataclass):
    assert job.id == 2
    assert job.progress == 100
    assert job.state == JobState.FINISHED


def get_object_from_json(json_file_name: str):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    path_dir = "{}{}{}".format(root_dir, os.sep, json_file_name)
    with open(path_dir) as f:
        data = json.load(f)
    return data
