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
import datetime

from qunicorn_core.api.api_models.job_dtos import JobCoreDto
from qunicorn_core.core.mapper import job_mapper, result_mapper
from qunicorn_core.db.database_services import db_service, device_db_service, deployment_db_service
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.db.models.result import ResultDataclass
from qunicorn_core.static.enums.job_state import JobState
from qunicorn_core.static.qunicorn_exception import QunicornError


# originally from <https://github.com/buehlefs/flask-template/>


def create_database_job(job_core: JobCoreDto) -> JobDataclass:
    """Creates a database job with the given circuit and saves it in the database"""
    db_job: JobDataclass = job_mapper.core_to_dataclass(job_core)
    db_job.state = JobState.READY
    db_job.progress = 0
    db_job.deployment = deployment_db_service.get_deployment_by_id(job_core.deployment.id)
    db_job.executed_on = device_db_service.get_device_by_name(job_core.executed_on.name)
    return db_service.save_database_object(db_job)


def update_attribute(job_id: int, attribute_value, attribute_name):
    """Updates one attribute (attribute_name) of the job with the id job_id"""
    db_service.get_session().query(JobDataclass).filter(JobDataclass.id == job_id).update(
        {attribute_name: attribute_value}
    )
    db_service.get_session().commit()


def update_finished_job(job_id: int, results: list[ResultDataclass], job_state: JobState = JobState.FINISHED):
    """Updates the attributes state and results of the job with the id job_id"""
    job: JobDataclass = get_job_by_id(job_id)
    job.finished_at = datetime.datetime.now()
    job.progress = 100
    job.results = results
    job.state = job_state
    db_service.save_database_object(job)


def get_job_by_id(job_id: int) -> JobDataclass:
    """Gets the job with the job_id from the database"""
    db_job = db_service.get_database_object_by_id(job_id, JobDataclass)
    if db_job is None:
        raise QunicornError("job_id '" + str(job_id) + "' can not be found")
    return db_job


def delete(id: int):
    """Removes one job"""
    db_service.remove_database_object_by_id(JobDataclass, id)


def get_all() -> list[JobDataclass]:
    """Gets all Jobs from the database"""
    return db_service.get_all_database_objects(JobDataclass)


def get_jobs_by_deployment_id(deployment_id: int) -> list[JobDataclass]:
    """Gets the job with the deployment_id from the database"""
    jobs = db_service.get_session().query(JobDataclass).filter(JobDataclass.deployment_id == deployment_id).all()
    db_service.get_session().commit()
    return jobs


def delete_jobs_by_deployment_id(deployment_id: int) -> list[JobDataclass]:
    """Gets the job with the deployment_id from the database"""
    job_ids = db_service.get_session().query(JobDataclass).filter(JobDataclass.deployment_id == deployment_id).delete()
    db_service.get_session().commit()
    return job_ids


def return_exception_and_update_job(job_id: int, exception: Exception) -> Exception:
    """Update job with id job_id in DB with error state and return the exception"""
    results = result_mapper.exception_to_error_results(exception)
    update_finished_job(job_id, results, JobState.ERROR)
    return exception
