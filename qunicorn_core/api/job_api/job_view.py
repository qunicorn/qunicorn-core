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

from flask.globals import current_app
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
    JobCommandSchema,
)
from ...core import job_service
from ...static.qunicorn_exception import QunicornError


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
        current_app.logger.info("Request: get all created jobs")
        return job_service.get_all_jobs(user_id=jwt_subject, status=status, deployment=deployment, device=device)

    @JOBMANAGER_API.arguments(JobFilterParamsSchema(only=["deployment"]), location="query", as_kwargs=True)
    @JOBMANAGER_API.arguments(JobRequestDtoSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.CREATED, SimpleJobDtoSchema())
    @JOBMANAGER_API.require_jwt(optional=True)
    def post(self, body: dict, jwt_subject: Optional[str], deployment: Optional[int] = None):
        """Create/Register and run new job.

        The deployment can be set in the body as `deploymentId`or with the query parameter `deployment`.
        If both are given, the query parameter will be used.
        """
        current_app.logger.info("Request: create and run new job")
        if deployment is not None:
            body["deployment_id"] = deployment
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
        current_app.logger.info(f"Request: get results of job with id: {job_id}")
        job_response_dto: JobResponseDto = job_service.get_job_by_id(job_id, user_id=jwt_subject)
        return job_response_dto

    @JOBMANAGER_API.response(HTTPStatus.NO_CONTENT)
    @JOBMANAGER_API.require_jwt(optional=True)
    def delete(self, job_id: int, jwt_subject: Optional[str]):
        """Delete job data via id and return the deleted job."""
        current_app.logger.info(f"Request: delete job with id: {job_id}")
        try:
            job_service.delete_job_data_by_id(job_id, user_id=jwt_subject)
        except QunicornError as err:
            if err.code == HTTPStatus.NOT_FOUND:
                # treat as deleted
                return
            raise err

    @JOBMANAGER_API.response(HTTPStatus.OK, JobResponseDtoSchema())
    @JOBMANAGER_API.arguments(JobCommandSchema(), location="json")
    @JOBMANAGER_API.require_jwt(optional=True)
    def post(self, command: dict, job_id: int, jwt_subject: Optional[str]):
        """Run, rerun or cancel an existing job.

        Commnad "run":
            Run job on IBM that was previously uploaded.

        Commnad "rerun":
            Create a new job on basis of an existing job and execute it.

        Commnad "cancel":
            Cancel a job execution via id.
        """
        token = command.pop("token", None)
        match command:
            case {"command": "run"}:
                current_app.logger.info(f"Request: run job with id: {job_id}")
                job_execution_dto: JobExecutePythonFileDto = JobExecutePythonFileDto(token=token)
                return job_service.run_job_by_id(job_id, job_execution_dto, user_id=jwt_subject)
            case {"command": "rerun"}:
                current_app.logger.info(f"Request: re run job with id: {job_id}")
                return job_service.re_run_job_by_id(job_id, token=token, user_id=jwt_subject)
            case {"command": "cancel"}:
                current_app.logger.info(f"Request: cancel job with id: {job_id}")
                return job_service.cancel_job_by_id(job_id, token=token, user_id=jwt_subject)
            case {"command": command}:
                raise QunicornError(f"Unknown command '{command}'.", HTTPStatus.BAD_REQUEST)
            case _:
                # check if JobCommandSchema and this match case are in sync!
                raise QunicornError("Bad command format!")


@JOBMANAGER_API.route("/<int:job_id>/results/")
class JobResultsView(MethodView):
    """Results endpoint of a single job."""

    @JOBMANAGER_API.response(HTTPStatus.OK, ResultDtoSchema(many=True))
    @JOBMANAGER_API.require_jwt(optional=True)
    def get(self, job_id: int, jwt_subject: Optional[str]):
        """Get the results of a job."""
        current_app.logger.info(f"Request: get results list of job with id: {job_id}")
        job_response_dto: JobResponseDto = job_service.get_job_by_id(job_id, user_id=jwt_subject)
        return job_response_dto.results


@JOBMANAGER_API.route("/<int:job_id>/results/<int:result_id>/")
class JobResultDetailView(MethodView):
    """Single result endpoint of a single job."""

    @JOBMANAGER_API.response(HTTPStatus.OK, ResultDtoSchema())
    @JOBMANAGER_API.require_jwt(optional=True)
    def get(self, result_id: int, job_id: int, jwt_subject: Optional[str]):
        """Get a single result of a job."""
        current_app.logger.info(f"Request: get result with id {result_id} of job with id: {job_id}")
        job_result_dto: ResultDto = job_service.get_job_result_by_id(result_id, job_id, user_id=jwt_subject)
        return job_result_dto


# TODO: remove the three following deprecated views later
@JOBMANAGER_API.route("/run/<int:job_id>/")
class JobRunView(MethodView):
    """Jobs endpoint to run a single job."""

    @JOBMANAGER_API.arguments(JobExecutionDtoSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, SimpleJobDtoSchema())
    @JOBMANAGER_API.doc(deprecated=True)
    @JOBMANAGER_API.require_jwt(optional=True)
    def post(self, body, job_id: int, jwt_subject: Optional[str]):
        """DEPRECATED! Use POST /jobs/<job_id>/ instead.

        Run job on IBM that was previously uploaded."""
        current_app.logger.info(f"Request: run job with id: {job_id}")
        job_execution_dto: JobExecutePythonFileDto = JobExecutePythonFileDto(**body)
        return job_service.run_job_by_id(job_id, job_execution_dto, user_id=jwt_subject)


@JOBMANAGER_API.route("/rerun/<int:job_id>/")
class JobReRunView(MethodView):
    """Jobs endpoint to rerun a single job."""

    @JOBMANAGER_API.arguments(TokenSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, SimpleJobDtoSchema())
    @JOBMANAGER_API.doc(deprecated=True)
    @JOBMANAGER_API.require_jwt(optional=True)
    def post(self, body, job_id: int, jwt_subject: Optional[str]):
        """DEPRECATED! Use POST /jobs/<job_id>/ instead.

        Create a new job on basis of an existing job and execute it."""
        current_app.logger.info(f"Request: re run job with id: {job_id}")
        return job_service.re_run_job_by_id(job_id, body["token"], user_id=jwt_subject)


@JOBMANAGER_API.route("/cancel/<int:job_id>/")
class JobCancelView(MethodView):
    """Jobs endpoint to cancel a single job."""

    @JOBMANAGER_API.arguments(TokenSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, SimpleJobDtoSchema())
    @JOBMANAGER_API.doc(deprecated=True)
    @JOBMANAGER_API.require_jwt(optional=True)
    def post(self, body, job_id: int, jwt_subject: Optional[str]):
        """DEPRECATED! Use POST /jobs/<job_id>/ instead.

        Cancel a job execution via id."""
        current_app.logger.info(f"Request: cancel job with id: {job_id}")
        return job_service.cancel_job_by_id(job_id, body["token"], user_id=jwt_subject)


# TODO: remove deprecated endpoint later
@JOBMANAGER_API.route("/queue/")
class JobQueueView(MethodView):
    """Jobs endpoint to get the queued jobs."""

    @JOBMANAGER_API.response(HTTPStatus.OK, QueuedJobsDtoSchema())
    @JOBMANAGER_API.doc(deprecated=True)
    @JOBMANAGER_API.require_jwt(optional=True)
    def get(self, jwt_subject: Optional[str]):
        """DEPRECATED! Use the "status" filter of the "/jobs/" route instead.

        Get the items of the job queue and the running job.
        """
        current_app.logger.info("Request: Get the items of the job queue and the running job")
        return job_service.get_job_queue_items(user_id=jwt_subject)
