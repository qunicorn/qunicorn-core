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


"""Module containing the routes of the job manager API."""
from http import HTTPStatus
from typing import Optional

from flask.views import MethodView

from .blueprint import JOBMANAGER_API
from ..api_models.job_dtos import (
    JobExecutePythonFileDto,
    JobExecutionDtoSchema,
    JobRequestDto,
    JobRequestDtoSchema,
    JobResponseDto,
    JobResponseDtoSchema,
    JobFilterParamsSchema,
    QueuedJobsDtoSchema,
    SimpleJobDto,
    SimpleJobDtoSchema,
    ResultDtoSchema,
    ResultDto,
    TokenSchema,
)
from ...core import job_service
from ...util import logging


@JOBMANAGER_API.route("/")
class JobIDView(MethodView):
    """Jobs endpoint for collection of all jobs."""

    @JOBMANAGER_API.arguments(JobFilterParamsSchema(), location="query", as_kwargs=True)
    @JOBMANAGER_API.response(HTTPStatus.OK, SimpleJobDtoSchema(many=True))
    @JOBMANAGER_API.require_jwt(optional=True)
    def get(
        self,
        jwt_subject: Optional[str],
        status: Optional[str] = None,
        deployment: Optional[int] = None,
        device: Optional[int] = None,
    ):
        """Get all created jobs."""
        logging.info("Request: get all created jobs")
        return job_service.get_all_jobs(user_id=jwt_subject, status=status, deployment=deployment, device=device)

    @JOBMANAGER_API.arguments(JobRequestDtoSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.CREATED, SimpleJobDtoSchema())
    @JOBMANAGER_API.require_jwt(optional=True)
    def post(self, body, jwt_subject: Optional[str]):
        """Create/Register and run new job."""
        logging.info("Request: create and run new job")
        job_dto: JobRequestDto = JobRequestDto(**body)
        job_response: SimpleJobDto = job_service.create_and_run_job(job_dto, user_id=jwt_subject)
        return job_response


@JOBMANAGER_API.route("/<int:job_id>/")
class JobDetailView(MethodView):
    """Jobs endpoint for a single job."""

    @JOBMANAGER_API.response(HTTPStatus.OK, JobResponseDtoSchema())
    @JOBMANAGER_API.require_jwt(optional=True)
    def get(self, job_id: int, jwt_subject: Optional[str]):
        """Get the details/results of a job."""
        logging.info(f"Request: get results of job with id: {job_id}")
        job_response_dto: JobResponseDto = job_service.get_job_by_id(job_id, user_id=jwt_subject)
        return job_response_dto

    @JOBMANAGER_API.response(HTTPStatus.OK, JobResponseDtoSchema())
    @JOBMANAGER_API.require_jwt(optional=True)
    def delete(self, job_id: int, jwt_subject: Optional[str]):
        """Delete job data via id and return the deleted job."""
        logging.info(f"Request: delete job with id: {job_id}")
        return job_service.delete_job_data_by_id(job_id, user_id=jwt_subject)


@JOBMANAGER_API.route("/<int:job_id>/results/")
class JobResultsView(MethodView):
    """Results endpoint of a single job."""

    @JOBMANAGER_API.response(HTTPStatus.OK, ResultDtoSchema(many=True))
    @JOBMANAGER_API.require_jwt(optional=True)
    def get(self, job_id: int, jwt_subject: Optional[str]):
        """Get the results of a job."""
        logging.info(f"Request: get results list of job with id: {job_id}")
        job_response_dto: JobResponseDto = job_service.get_job_by_id(job_id, user_id=jwt_subject)
        return job_response_dto.results


@JOBMANAGER_API.route("/<int:job_id>/results/<int:result_id>/")
class JobResultDetailView(MethodView):
    """Single result endpoint of a single job."""

    @JOBMANAGER_API.response(HTTPStatus.OK, ResultDtoSchema())
    @JOBMANAGER_API.require_jwt(optional=True)
    def get(self, result_id: int, job_id: int, jwt_subject: Optional[str]):
        """Get a single result of a job."""
        logging.info(f"Request: get result with id {result_id} of job with id: {job_id}")
        job_result_dto: ResultDto = job_service.get_job_result_by_id(result_id, job_id, user_id=jwt_subject)
        return job_result_dto


# FIXME: merge the three following views under /<int:job_id>/ into one post method!
@JOBMANAGER_API.route("/run/<int:job_id>/")
class JobRunView(MethodView):
    """Jobs endpoint to run a single job."""

    @JOBMANAGER_API.arguments(JobExecutionDtoSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, SimpleJobDtoSchema())
    @JOBMANAGER_API.require_jwt(optional=True)
    def post(self, body, job_id: int, jwt_subject: Optional[str]):
        """DEPRECATED! Run job on IBM that was previously uploaded."""
        logging.info(f"Request: run job with id: {job_id}")
        job_execution_dto: JobExecutePythonFileDto = JobExecutePythonFileDto(**body)
        return job_service.run_job_by_id(job_id, job_execution_dto, user_id=jwt_subject)


@JOBMANAGER_API.route("/rerun/<int:job_id>/")
class JobReRunView(MethodView):
    """Jobs endpoint to rerun a single job."""

    @JOBMANAGER_API.arguments(TokenSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, SimpleJobDtoSchema())
    @JOBMANAGER_API.require_jwt(optional=True)
    def post(self, body, job_id: int, jwt_subject: Optional[str]):
        """DEPRECATED! Create a new job on basis of an existing job and execute it."""
        logging.info(f"Request: re run job with id: {job_id}")
        return job_service.re_run_job_by_id(job_id, body["token"], user_id=jwt_subject)


@JOBMANAGER_API.route("/cancel/<int:job_id>/")
class JobCancelView(MethodView):
    """Jobs endpoint to cancel a single job."""

    @JOBMANAGER_API.arguments(TokenSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, SimpleJobDtoSchema())
    @JOBMANAGER_API.require_jwt(optional=True)
    def post(self, body, job_id: int, jwt_subject: Optional[str]):
        """DEPRECATED! Cancel a job execution via id."""
        logging.info(f"Request: cancel job with id: {job_id}")
        return job_service.cancel_job_by_id(job_id, body["token"], user_id=jwt_subject)


# FIXME: make this a query param in the JobIDView
@JOBMANAGER_API.route("/queue/")
class JobQueueView(MethodView):
    """Jobs endpoint to get the queued jobs."""

    @JOBMANAGER_API.response(HTTPStatus.OK, QueuedJobsDtoSchema())
    @JOBMANAGER_API.require_jwt(optional=True)
    def get(self, jwt_subject: Optional[str]):
        """DEPRECATED! Use the "status" filter of the "/jobs/" route instead.

        Get the items of the job queue and the running job.
        """
        logging.info("Request: Get the items of the job queue and the running job")
        return job_service.get_job_queue_items(user_id=jwt_subject)
