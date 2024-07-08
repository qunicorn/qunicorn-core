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


"""Module containing the routes of the deployments API."""

from http import HTTPStatus
from typing import Optional

from flask.globals import current_app
from flask.views import MethodView

from .blueprint import DEPLOYMENT_API
from ..api_models import SimpleJobDtoSchema
from ..api_models.deployment_dtos import (
    DeploymentDtoSchema,
    DeploymentUpdateDto,
    DeploymentUpdateDtoSchema,
    SimpleDeploymentDtoSchema,
    DeploymentFilterParamsSchema,
    QuantumProgramDtoSchema,
)
from ...core import deployment_service, job_service
from ...static.qunicorn_exception import QunicornError


@DEPLOYMENT_API.route("/")
class DeploymentIDView(MethodView):
    """Deployments endpoint for collection of all deployed jobs."""

    @DEPLOYMENT_API.arguments(DeploymentFilterParamsSchema(), location="query", as_kwargs=True)
    @DEPLOYMENT_API.response(HTTPStatus.OK, SimpleDeploymentDtoSchema(many=True))
    @DEPLOYMENT_API.require_jwt(optional=True)
    def get(self, jwt_subject: Optional[str], name: Optional[str] = None, page: int = 1, item_count: int = 100):
        """Get the list of deployments."""
        current_app.logger.info("Request: get all deployments")
        deployments = deployment_service.get_all_deployment_responses(
            user_id=jwt_subject, name=name, page=page, item_count=item_count
        )
        if page > 1 and not deployments:
            raise QunicornError(f"Page {page} not found.", HTTPStatus.NOT_FOUND)
        return deployments

    @DEPLOYMENT_API.arguments(DeploymentUpdateDtoSchema(), location="json")
    @DEPLOYMENT_API.response(HTTPStatus.CREATED, SimpleDeploymentDtoSchema())
    @DEPLOYMENT_API.require_jwt(optional=True)
    def post(self, body, jwt_subject: Optional[str]):
        """Create/Deploy new Job-definition."""
        current_app.logger.info("Request: create new deployment")
        deployment_dto: DeploymentUpdateDto = DeploymentUpdateDto.from_dict(body)
        return deployment_service.create_deployment(deployment_dto, user_id=jwt_subject)


@DEPLOYMENT_API.route("/<int:deployment_id>/")
class DeploymentDetailView(MethodView):
    """API endpoint for single pre-deployments."""

    @DEPLOYMENT_API.response(HTTPStatus.OK, DeploymentDtoSchema)
    @DEPLOYMENT_API.require_jwt(optional=True)
    def get(self, deployment_id: int, jwt_subject: Optional[str]):
        """Get detailed information for single deployed job-definition."""
        current_app.logger.info("Request: get deployment by id")
        return deployment_service.get_deployment_by_id(deployment_id, user_id=jwt_subject)

    @DEPLOYMENT_API.response(HTTPStatus.NO_CONTENT)
    @DEPLOYMENT_API.require_jwt(optional=True)
    def delete(self, deployment_id: int, jwt_subject: Optional[str]):
        """Delete single deployment by ID."""
        current_app.logger.info("Request: delete deployment by id")
        try:
            deployment_service.delete_deployment(deployment_id, user_id=jwt_subject)
        except QunicornError as err:
            if err.code == HTTPStatus.NOT_FOUND:
                # treat as deleted
                return
            raise err

    @DEPLOYMENT_API.response(HTTPStatus.OK, DeploymentDtoSchema)
    @DEPLOYMENT_API.arguments(DeploymentUpdateDtoSchema(), location="json")
    @DEPLOYMENT_API.require_jwt(optional=True)
    def put(self, body, deployment_id: int, jwt_subject: Optional[str]):
        """Update single deployment by ID."""
        current_app.logger.info("Request: update deployment by id")
        deployment_dto: DeploymentUpdateDto = DeploymentUpdateDto.from_dict(body)
        return deployment_service.update_deployment(deployment_dto, deployment_id, user_id=jwt_subject)


@DEPLOYMENT_API.route("/<int:deployment_id>/programs/")
class DeploymentProgramsView(MethodView):

    @DEPLOYMENT_API.response(HTTPStatus.OK, QuantumProgramDtoSchema(many=True))
    @DEPLOYMENT_API.require_jwt(optional=True)
    def get(self, deployment_id: int, jwt_subject: Optional[str]):
        """Get the programs of a single deployed job-definition."""
        current_app.logger.info("Request: get deployment programs by deployment id")
        return deployment_service.get_deployment_by_id(deployment_id, user_id=jwt_subject).programs


@DEPLOYMENT_API.route("/<int:deployment_id>/programs/<int:program_id>/")
class DeploymentProgramDetailsView(MethodView):

    @DEPLOYMENT_API.response(HTTPStatus.OK, QuantumProgramDtoSchema())
    @DEPLOYMENT_API.require_jwt(optional=True)
    def get(self, deployment_id: int, program_id: int, jwt_subject: Optional[str]):
        """Get the programs of a single deployed job-definition."""
        current_app.logger.info("Request: get deployment program by id")
        return deployment_service.get_program_by_id(program_id, deployment_id, user_id=jwt_subject)


@DEPLOYMENT_API.route("/<int:deployment_id>/jobs/")
class JobsByDeploymentView(MethodView):
    """API endpoint for jobs of a specific deployment."""

    @DEPLOYMENT_API.response(HTTPStatus.OK, SimpleJobDtoSchema(many=True))
    @DEPLOYMENT_API.require_jwt(optional=True)
    def get(self, deployment_id: str, jwt_subject: Optional[str]):
        """Get the details of all jobs with a specific deployment id."""
        current_app.logger.info("Request: get jobs with deployment id")
        jobs_by_deployment_id = job_service.get_jobs_by_deployment_id(deployment_id, user_id=jwt_subject)
        return jobs_by_deployment_id

    @DEPLOYMENT_API.response(HTTPStatus.OK, SimpleJobDtoSchema(many=True))
    @DEPLOYMENT_API.require_jwt(optional=True)
    def delete(self, deployment_id: str, jwt_subject: Optional[str]):
        """Delete all jobs with a specific deployment id."""
        current_app.logger.info("Request: delete jobs with deployment id")
        jobs_by_deployment_id = job_service.delete_jobs_by_deployment_id(deployment_id, user_id=jwt_subject)
        return jobs_by_deployment_id
