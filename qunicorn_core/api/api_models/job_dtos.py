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
from typing import Optional

import marshmallow as ma
from flask import url_for
from marshmallow.validate import OneOf, Range

from .device_dtos import DeviceDto, DeviceDtoSchema
from .result_dtos import ResultDto, ResultDtoSchema
from ..flask_api_utils import MaBaseSchema

__all__ = [
    "SimpleJobDtoSchema",
    "SimpleJobDto",
    "JobResponseDtoSchema",
    "JobRequestDtoSchema",
    "JobResponseDto",
    "JobRequestDto",
    "TokenSchema",
    "JobExecutePythonFileDto",
    "JobExecutionDtoSchema",
    "JobFilterParamsSchema",
    "QueuedJobsDtoSchema",
    "JobCommandSchema",
]

from ...static.enums.error_mitigation import ErrorMitigationMethod

from ...static.enums.job_state import JobState
from ...static.enums.job_type import JobType
from ...static.enums.provider_name import ProviderName


@dataclass
class JobRequestDto:
    """JobDto that was sent from the user as a request"""

    name: str
    provider_name: str
    device_name: str
    shots: int
    token: str
    error_mitigation: ErrorMitigationMethod
    cut_to_width: Optional[int]
    type: JobType
    deployment_id: int


@dataclass
class JobResponseDto:
    """JobDto that is sent to the user as a response"""

    id: int
    deployment_id: Optional[int]
    executed_by: Optional[str]
    executed_on: DeviceDto
    progress: int
    state: str
    type: JobType
    started_at: datetime
    finished_at: Optional[datetime]
    name: Optional[str]
    results: list[ResultDto]


@dataclass
class SimpleJobDto:
    id: Optional[int]
    deployment_id: Optional[int]
    name: Optional[str]
    state: JobState = JobState.RUNNING


@dataclass
class JobExecutePythonFileDto:
    token: str | None = None
    python_file_options: str | None = None
    python_file_inputs: str | None = None


class JobRequestDtoSchema(MaBaseSchema):
    name = ma.fields.String(required=True, metadata={"example": "JobName"})
    provider_name = ma.fields.Enum(required=True, metadata={"example": ProviderName.IBM}, enum=ProviderName)
    device_name = ma.fields.String(required=True, metadata={"example": "aer_simulator"})
    shots = ma.fields.Int(
        required=False,
        allow_none=True,
        metadata={"example": 4000, "label": "shots", "description": "number of shots", "input_type": "number"},
    )
    error_mitigation = ma.fields.Enum(
        required=False,
        metadata={"example": ErrorMitigationMethod.none},
        enum=ErrorMitigationMethod,
        load_default=ErrorMitigationMethod.none,
        dump_default=ErrorMitigationMethod.none,
    )
    cut_to_width = ma.fields.Int(required=False, allow_none=True, missing=None, metadata={"example": None})
    token = ma.fields.String(required=True, metadata={"example": ""})
    type = ma.fields.Enum(required=True, metadata={"example": JobType.RUNNER}, enum=JobType)
    deployment_id = ma.fields.Integer(required=False, allow_none=True, metadata={"example": 1})


class JobResponseDtoSchema(MaBaseSchema):
    id = ma.fields.Int(required=True, dump_only=True)
    name = ma.fields.String(required=True, dump_default="", dump_only=True)
    executed_by = ma.fields.String(required=False, dump_only=True)
    executed_on = ma.fields.Nested(DeviceDtoSchema())
    progress = ma.fields.Int(required=True, dump_only=True)
    state = ma.fields.String(required=True, dump_only=True)
    type = ma.fields.String(required=True, dump_only=True)
    started_at = ma.fields.AwareDateTime(required=True, dump_only=True)
    finished_at = ma.fields.AwareDateTime(required=True, allow_none=True, dump_only=True)
    results = ma.fields.Nested(ResultDtoSchema(exclude=["job"]), many=True, required=True, dump_only=True)
    self = ma.fields.Function(lambda obj: url_for("job-api.JobDetailView", job_id=obj.id))
    deplyoment = ma.fields.Function(
        lambda obj: url_for("deployment-api.DeploymentDetailView", deployment_id=obj.deployment_id)
    )


class SimpleJobDtoSchema(MaBaseSchema):
    id = ma.fields.Integer(required=True, allow_none=False, dump_only=True)
    name = ma.fields.String(required=False, allow_none=False, dump_only=True)
    state = ma.fields.String(required=False, allow_none=False, dump_only=True)
    self = ma.fields.Function(lambda obj: url_for("job-api.JobDetailView", job_id=obj.id))
    deplyoment = ma.fields.Function(
        lambda obj: url_for("deployment-api.DeploymentDetailView", deployment_id=obj.deployment_id)
    )


class JobFilterParamsSchema(MaBaseSchema):
    status = ma.fields.String(required=False, missing=None, load_only=True, validate=OneOf([s.value for s in JobState]))
    deployment = ma.fields.Integer(required=False, missing=None, load_only=True)
    device = ma.fields.Integer(required=False, missing=None, load_only=True)
    page = ma.fields.Integer(
        required=False,
        missing=1,
        load_only=True,
        validate=Range(min=0),
        description="Page numbers range from 1 for the first page to n.",
        metadata={"example": 1},
    )
    item_count = ma.fields.Integer(
        data_key="item-count",
        required=False,
        missing=100,
        load_only=True,
        validate=Range(min=1, max=1000, min_inclusive=True, max_inclusive=True),
        description="The number of items per page (can be set between 1 and 1000, defaults to 100).",
        metadata={"example": 100},
    )


class TokenSchema(MaBaseSchema):
    token = ma.fields.String(required=True, metadata={"example": ""})


class JobExecutionDtoSchema(MaBaseSchema):
    token = ma.fields.String(required=True, metadata={"example": ""})
    python_file_options = ma.fields.Dict(required=True, metadata={"example": {"backend": "ibmq_qasm_simulator"}})
    python_file_inputs = ma.fields.Dict(required=True)


class QueuedJobsDtoSchema(MaBaseSchema):
    running_job = ma.fields.Nested(SimpleJobDtoSchema)
    queued_jobs = ma.fields.List(ma.fields.Nested(SimpleJobDtoSchema))


class JobCommandSchema(MaBaseSchema):
    command = ma.fields.String(
        required=True, validate=OneOf(["run", "rerun", "cancel"]), metadata={"example": "cancel"}
    )
    token = ma.fields.String(required=False, allow_none=True, missing=None, metadata={"example": ""})
