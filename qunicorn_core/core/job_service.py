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
from datetime import datetime, timezone
from os import environ
from http import HTTPStatus
from typing import Optional, Sequence

from flask.globals import current_app

from qunicorn_core.api.api_models.job_dtos import (
    JobExecutePythonFileDto,
    JobRequestDto,
    JobResponseDto,
    SimpleJobDto,
    ResultDto,
)
from qunicorn_core.core import job_manager_service
from qunicorn_core.core.mapper import job_mapper, result_mapper
from qunicorn_core.db.db import DB
from qunicorn_core.db.models.deployment import DeploymentDataclass
from qunicorn_core.db.models.device import DeviceDataclass
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.db.models.job_state import TransientJobStateDataclass
from qunicorn_core.db.models.result import ResultDataclass
from qunicorn_core.static.enums.job_state import JobState
from qunicorn_core.static.enums.job_type import JobType
from qunicorn_core.static.qunicorn_exception import QunicornError
from qunicorn_core.util.utils import is_running_asynchronously

"""
This module contains the service layer for jobs. It is used to create and run jobs.
It calls the job_manager_service to run the jobs with celery.
"""


# TODO: make this an option that is managed in the app config
ASYNCHRONOUS: bool = environ.get("EXECUTE_CELERY_TASK_ASYNCHRONOUS") == "True"


def create_and_run_job(
    job_request_dto: JobRequestDto, is_asynchronous: bool = ASYNCHRONOUS, user_id: Optional[str] = None
) -> SimpleJobDto:
    """First creates a job to let it run afterwards on a pilot"""
    device: Optional[DeviceDataclass] = DeviceDataclass.get_by_name(
        job_request_dto.device_name, job_request_dto.provider_name
    )
    if device is None:
        raise QunicornError(
            f"Could not find device '{job_request_dto.device_name}' of provider '{job_request_dto.provider_name}'!"
        )
    deployment: DeploymentDataclass = DeploymentDataclass.get_by_id_authenticated_or_404(
        job_request_dto.deployment_id, user_id
    )

    job: JobDataclass = JobDataclass(
        name=job_request_dto.name,
        shots=job_request_dto.shots,
        type=job_request_dto.type.name,
        executed_by=user_id,
        executed_on=device,
        deployment=deployment,
        progress=0,
        state=JobState.READY,
        started_at=datetime.now(timezone.utc),
        results=[],
    )

    if not is_asynchronous:
        job.celery_id = "synchronous"
    job.save(commit=True)
    run_job_with_celery(job, is_asynchronous, token=job_request_dto.token)
    return SimpleJobDto(id=job.id, deployment_id=job.deployment_id, name=job.name, state=JobState.READY)


def run_job_with_celery(job: JobDataclass, is_asynchronous: bool, token: Optional[str] = None):
    """Serialize the job and run it with celery"""
    assert len(job._transient) == 0, "jobs should not have any state attached by default"
    if token is not None:
        state = TransientJobStateDataclass(job=job, data={"token": token})
        state.save(commit=True)  # make sure token is immediately available in DB

    if is_asynchronous:
        task = job_manager_service.run_job.delay(job.id)
        job.celery_id = task.id
        job.save(commit=True)
    else:
        job_manager_service.run_job(job.id)


def re_run_job_by_id(job_id: int, token: Optional[str], user_id: Optional[str] = None) -> SimpleJobDto:
    """Get job from DB, Save it as new job and run it with the new id"""
    job: JobDataclass = JobDataclass.get_by_id_authenticated_or_404(job_id, user_id)
    if token is None:
        token = ""
    job_request: JobRequestDto = JobRequestDto(
        name=job.name,
        deployment_id=job.deployment_id,
        provider_name=job.executed_on.provider.name,
        device_name=job.executed_on.name,
        shots=job.shots,
        token=token,
        type=JobType(job.type),
    )
    return create_and_run_job(job_request)


def run_job_by_id(
    job_id: int, job_exec_dto: JobExecutePythonFileDto, asyn: bool = ASYNCHRONOUS, user_id: Optional[str] = None
) -> SimpleJobDto:
    """EXPERIMENTAL: Get uploaded job from DB, and run it on a provider"""
    job: JobDataclass = JobDataclass.get_by_id_authenticated_or_404(job_id, user_id)
    if not asyn:
        job.celery_id = "synchronous"
    job.save(commit=True)
    run_job_with_celery(job, asyn, token=job_exec_dto.token)
    return SimpleJobDto(id=job.id, deployment_id=job.deployment_id, name=job.name, state=JobState.RUNNING)


def get_job_by_id(job_id: int, user_id: Optional[str]) -> JobResponseDto:
    """Gets the job from the database service with its id"""
    db_job: JobDataclass = JobDataclass.get_by_id_authenticated_or_404(job_id, user_id)
    return job_mapper.dataclass_to_response(db_job)


def get_job_result_by_id(result_id: int, job_id: int, user_id: Optional[str]) -> ResultDto:
    result: ResultDataclass = ResultDataclass.get_by_id_authenticated_or_404(result_id, user_id)
    if result.job_id != job_id:
        raise QunicornError(f"Result with id {result_id} for job with id {job_id} not found.", HTTPStatus.NOT_FOUND)
    return result_mapper.dataclass_to_dto(result)


def delete_job_data_by_id(job_id, user_id: Optional[str]):
    """delete job data from db"""
    job = JobDataclass.get_by_id_authenticated_or_404(job_id, user_id)
    job.delete(commit=True)


def get_all_jobs(
    user_id: Optional[str], status: Optional[str] = None, deployment: Optional[int] = None, device: Optional[int] = None
) -> list[SimpleJobDto]:
    """get all jobs from the db"""
    where = []
    if status:
        where.append(JobDataclass.state == status)
    if deployment is not None:
        where.append(JobDataclass.deployment_id == deployment)
    if device is not None:
        where.append(JobDataclass.executed_on_id == device)
    return [
        job_mapper.dataclass_to_simple(job)
        for job in JobDataclass.get_all_authenticated(user_id, where=where)
        if job.executed_by is None or job.executed_by == user_id
    ]


def cancel_job_by_id(job_id, token: Optional[str], user_id: Optional[str] = None) -> SimpleJobDto:
    """cancel job execution"""
    current_app.logger.info(f"Cancel execution of job with id: {job_id}")
    job: JobDataclass = JobDataclass.get_by_id_authenticated_or_404(job_id, user_id)
    job_manager_service.cancel_job(job, token, user_id)
    return SimpleJobDto(id=job.id, deployment_id=job.deployment_id, name=job.name, state=JobState.CANCELED)


def get_jobs_by_deployment_id(deployment_id, user_id: Optional[str] = None) -> list[SimpleJobDto]:
    """get all jobs of a deployment that the user is authorized to with the id deployment_id"""
    jobs_by_deployment_id = JobDataclass.get_by_deployment_authenticated(deployment_id, user_id)
    return [job_mapper.dataclass_to_simple(job) for job in jobs_by_deployment_id]


def delete_jobs_by_deployment_id(deployment_id, user_id: Optional[str] = None) -> list[SimpleJobDto]:
    """delete all jobs of a deployment that the user is authorized to with the id deployment_id"""
    jobs = JobDataclass.get_by_deployment_authenticated(deployment_id, user_id=user_id)
    for job in jobs:
        job.delete()
    DB.session.commit()
    return [job_mapper.dataclass_to_simple(job) for job in jobs]


def get_job_queue_items(user_id: Optional[str]) -> dict:
    """Get the latest running job and all latest ready jobs"""
    if not is_running_asynchronously():
        raise QunicornError("Returning queued jobs is not possible in synchronous mode", status_code=400)
    all_jobs: Sequence[JobDataclass] = JobDataclass.get_all_authenticated(user_id)
    return {"running_job": get_latest_running_job(all_jobs), "queued_jobs": get_latest_ready_jobs(all_jobs)}


# TODO: implement filter in DB query?
def get_latest_ready_jobs(all_jobs: Sequence[JobDataclass]) -> list[SimpleJobDto]:
    """Get all latest jobs with state ready until reaching the first finished job"""
    latest_jobs: list[SimpleJobDto] = []
    for job in sorted(all_jobs, reverse=True, key=lambda j: j.id):
        if job.state == JobState.READY:
            latest_jobs.append(job_mapper.dataclass_to_simple(job))
        elif job.state == JobState.FINISHED:
            break
    latest_jobs.sort(key=lambda j: j.id)
    return latest_jobs


# TODO: implement filter in DB query?
def get_latest_running_job(all_jobs: Sequence[JobDataclass]) -> SimpleJobDto | None:
    """Get the latest job with state running, check until reaching the first finished job"""
    for job in all_jobs:
        if job.state == JobState.RUNNING:
            return job_mapper.dataclass_to_simple(job)
        elif job.state == JobState.FINISHED:
            return None
    return None
