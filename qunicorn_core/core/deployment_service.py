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
from http import HTTPStatus
from typing import Optional

from qunicorn_core.api.api_models import DeploymentDto, DeploymentUpdateDto, QuantumProgramDto
from qunicorn_core.core.mapper import deployment_mapper, quantum_program_mapper
from qunicorn_core.db.models.deployment import DeploymentDataclass
from qunicorn_core.db.models.quantum_program import QuantumProgramDataclass
from qunicorn_core.static.qunicorn_exception import QunicornError


def get_all_deployments(user_id: Optional[str] = None) -> list[DeploymentDto]:
    """Gets all deployments that a user is authorized to see"""
    deployment_list: list[DeploymentDto] = [
        deployment_mapper.dataclass_to_dto(d) for d in DeploymentDataclass.get_all_authenticated(user_id)
    ]
    return deployment_list


def get_deployment_by_id(deployment_id: int, user_id: Optional[str] = None) -> DeploymentDto:
    """Gets one deployment by id if the user is authorized to see it"""
    deployment = DeploymentDataclass.get_by_id_authenticated_or_404(deployment_id, user_id)
    return deployment_mapper.dataclass_to_dto(deployment)


def get_program_by_id(program_id: int, deployment_id: int, user_id: Optional[str] = None) -> QuantumProgramDto:
    """Gets one program of a deployment by id if the user is authorized to see it"""
    program = QuantumProgramDataclass.get_by_id_authenticated_or_404(program_id, user_id)
    if program.deployment_id != deployment_id:
        raise QunicornError(
            f"Program with id {program_id} for deployment with id {deployment_id} not found.", HTTPStatus.NOT_FOUND
        )
    return quantum_program_mapper.dataclass_to_dto(program)


def get_all_deployment_responses(
    user_id: Optional[str] = None, name: Optional[str] = None, page: int = 1, item_count: int = 100
) -> list[DeploymentDto]:
    """Gets all deployments from a user as responses to clearly arrange them in the frontend"""
    where = []
    if name:
        if "%" in name:
            where.append(DeploymentDataclass.name.like(name, escape="\\"))
        else:
            where.append(DeploymentDataclass.name == name)
    page_offset = (page - 1) * item_count
    deployment_list: list[DeploymentDto] = [
        deployment_mapper.dataclass_to_dto(d)
        for d in DeploymentDataclass.get_all_authenticated(user_id, where=where, limit=item_count, offset=page_offset)
    ]
    return deployment_list


def update_deployment(
    deployment_dto: DeploymentUpdateDto, deployment_id: int, user_id: Optional[str] = None
) -> DeploymentDto:
    """Updates one deployment"""
    try:
        db_deployment = DeploymentDataclass.get_by_id_authenticated_or_404(deployment_id, user_id)
        db_deployment.deployed_at = datetime.now(timezone.utc)
        db_deployment.name = deployment_dto.name
        db_deployment.programs = [
            QuantumProgramDataclass(
                assembler_language=qc.assembler_language.name if qc.assembler_language else None,
                quantum_circuit=qc.quantum_circuit,
                python_file_path=qc.python_file_path,
                python_file_metadata=qc.python_file_metadata,
            )
            for qc in deployment_dto.programs
        ]
        for p in db_deployment.programs:
            p.save()  # add programs to session
        db_deployment.save(commit=True)
        return deployment_mapper.dataclass_to_dto(db_deployment)
    except AttributeError:
        raise QunicornError(
            "Error updating deployment with id: " + str(deployment_id), HTTPStatus.INTERNAL_SERVER_ERROR
        )


def delete_deployment(deployment_id: int, user_id: Optional[str] = None):
    """Remove one deployment by id."""
    db_deployment = DeploymentDataclass.get_by_id_authenticated_or_404(deployment_id, user_id)
    if len(db_deployment.jobs) > 0:
        raise QunicornError("Deployment is in use by a job", HTTPStatus.BAD_REQUEST)
    db_deployment.delete(commit=True)


def create_deployment(deployment_dto: DeploymentUpdateDto, user_id: Optional[str] = None) -> DeploymentDto:
    """Create a deployment and save it in the database"""
    programs = [
        QuantumProgramDataclass(
            assembler_language=qc.assembler_language.value if qc.assembler_language else None,
            quantum_circuit=qc.quantum_circuit,
            python_file_path=qc.python_file_path,
            python_file_metadata=qc.python_file_metadata,
        )
        for qc in deployment_dto.programs
    ]
    deployment: DeploymentDataclass = DeploymentDataclass(
        name=deployment_dto.name,
        deployed_at=datetime.now(timezone.utc),
        programs=programs,
        deployed_by=user_id,
    )
    for p in deployment.programs:
        p.save()
    deployment.save(commit=True)
    return deployment_mapper.dataclass_to_dto(deployment)
