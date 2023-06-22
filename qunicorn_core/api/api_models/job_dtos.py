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


"""Module containing all Dtos and their Schemas for tasks in the Jobmanager API."""
from dataclasses import dataclass
from datetime import datetime

import marshmallow as ma
from marshmallow import fields, ValidationError
from qiskit import QuantumCircuit

from .deployment_dtos import DeploymentDto
from .device_dtos import DeviceDto
from .user_dtos import UserDto
from ..util import MaBaseSchema

__all__ = [
    "JobIDSchema",
    "JobID",
    "JobResponseDtoSchema",
    "JobRequestDtoSchema",
    "JobCoreDto",
    "JobResponseDto",
    "JobRequestDto",
]

from ...static.enums.job_state import JobState
from ...static.enums.provider_name import ProviderName


@dataclass
class JobRequestDto:
    name: str
    circuit: str
    provider_name: str
    shots: int
    parameters: str
    token: str


@dataclass
class JobCoreDto:
    id: int
    executed_by: UserDto
    executed_on: DeviceDto
    deployment: DeploymentDto
    progress: str
    state: str
    shots: int
    started_at: datetime
    finished_at: datetime
    name: str
    data: str
    results: str
    parameters: str
    token: str | None = None


@dataclass
class JobResponseDto:
    id: int
    executed_by: str
    executed_on: str
    progress: str
    state: str
    started_at: datetime
    finished_at: datetime
    name: str
    data: str
    results: str
    parameters: str


@dataclass
class JobID:
    id: str
    name: str
    job_state: str = JobState.RUNNING


class CircuitField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, str) or isinstance(value, list):
            return value
        else:
            raise ValidationError("Field should be str or list")


def get_quasm_string() -> str:
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc.qasm()


class JobRequestDtoSchema(MaBaseSchema):
    name = ma.fields.String(required=True, example="JobName")
    circuit = CircuitField(required=True, example=get_quasm_string())
    provider_name = ma.fields.Enum(required=True, example="IBM", enum=ProviderName)
    shots = ma.fields.Int(
        required=False,
        allow_none=True,
        metada={
            "label": "Shots",
            "description": "Number of shots",
            "input_type": "number",
        },
        example=4000,
    )
    parameters = ma.fields.List(ma.fields.Float(), required=False)
    token = ma.fields.String(required=True, example="")


class JobResponseDtoSchema(MaBaseSchema):
    id = ma.fields.Int(required=True, dump_only=True)
    executed_by = ma.fields.String(required=True, dump_only=True)
    executed_on = ma.fields.String(required=True, dump_only=True)
    progress = ma.fields.Int(required=True, dump_only=True)
    state = ma.fields.String(required=True, dump_only=True)
    started_at = ma.fields.String(required=True, dump_only=True)
    finished_at = ma.fields.String(required=True, dump_only=True)
    data = ma.fields.String(required=True, dump_only=True)
    results = ma.fields.String(required=True, dump_only=True)
    parameters = ma.fields.String(required=True, dump_only=True)


class JobIDSchema(MaBaseSchema):
    id = ma.fields.Integer(required=True, allow_none=False, dump_only=True, example=123)
    job_name = ma.fields.String(required=False, allow_none=False, dump_only=True)
    job_state = ma.fields.String(required=False, allow_none=False, dump_only=True)