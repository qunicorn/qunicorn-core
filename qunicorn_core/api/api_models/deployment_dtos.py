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


"""Module containing all Dtos and their Schemas for tasks in the Deployment API."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from flask import url_for
import marshmallow as ma

from .quantum_program_dtos import (
    QuantumProgramDto,
    QuantumProgramDtoSchema,
    QuantumProgramRequestDto,
    QuantumProgramRequestDtoSchema,
)
from ...static.enums.assembler_languages import AssemblerLanguage
from ..flask_api_utils import MaBaseSchema

__all__ = [
    "DeploymentDtoSchema",
    "DeploymentUpdateDtoSchema",
    "DeploymentDto",
    "DeploymentUpdateDto",
    "SimpleDeploymentDtoSchema",
]


@dataclass
class DeploymentDto:
    id: int
    programs: list[QuantumProgramDto]
    deployed_by: Optional[str]
    deployed_at: datetime
    name: Optional[str]


@dataclass
class DeploymentUpdateDto:
    programs: list[QuantumProgramRequestDto]
    name: str

    @staticmethod
    def from_dict(body: dict) -> "DeploymentUpdateDto":
        deployment_dto: DeploymentUpdateDto = DeploymentUpdateDto(**body)
        deployment_dto.programs = [
            QuantumProgramRequestDto(
                quantum_circuit=program["quantum_circuit"],
                assembler_language=AssemblerLanguage(program["assembler_language"]),
                python_file_path=program.get("python_file_path"),
                python_file_metadata=program.get("python_file_metadata"),
            )
            for program in body["programs"]
        ]
        return deployment_dto


class DeploymentDtoSchema(MaBaseSchema):
    id = ma.fields.Integer(required=True, metadata={"description": "UID for the deployment_api"})
    deployed_by = ma.fields.String(required=False, metadata={"description": "Optional id of the user who created it"})
    programs = ma.fields.Nested(QuantumProgramDtoSchema(many=True, exclude=["deployment"]))
    deployed_at = ma.fields.AwareDateTime(required=True, metadata={"description": "time of deployment"})
    name = ma.fields.String(
        required=False,
        metadata={"description": "an optional name for the deployment_api."},
    )
    self = ma.fields.Function(lambda obj: url_for("deployment-api.DeploymentDetailView", deployment_id=obj.id))
    jobs = ma.fields.Function(lambda obj: url_for("deployment-api.JobsByDeploymentView", deployment_id=obj.id))


class DeploymentUpdateDtoSchema(MaBaseSchema):
    programs = ma.fields.Nested(QuantumProgramRequestDtoSchema(many=True))
    name = ma.fields.String(
        required=True,
        metadata={"example": "DeploymentName", "description": "an optional name for the deployment_api."},
    )


class SimpleDeploymentDtoSchema(MaBaseSchema):
    id = ma.fields.Integer(dump_only=True)
    programs = ma.fields.List(
        ma.fields.Nested(QuantumProgramDtoSchema(only=["id", "self", "assembler_language"])), dump_only=True
    )
    name = ma.fields.String(dump_only=True)
    self = ma.fields.Function(lambda obj: url_for("deployment-api.DeploymentDetailView", deployment_id=obj.id))
