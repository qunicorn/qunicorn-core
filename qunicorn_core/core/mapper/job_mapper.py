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

from qunicorn_core.api.api_models.job_dtos import JobResponseDto, SimpleJobDto
from qunicorn_core.core.mapper import device_mapper, result_mapper
from qunicorn_core.db.models.job import JobDataclass
from qunicorn_core.static.enums.job_state import JobState
from qunicorn_core.static.enums.job_type import JobType


def dataclass_to_response(job: JobDataclass) -> JobResponseDto:
    return JobResponseDto(
        id=job.id,
        deployment_id=job.deployment_id,
        executed_by=job.executed_by,
        executed_on=device_mapper.dataclass_to_dto(job.executed_on) if job.executed_on else None,
        progress=job.progress,
        state=JobState(job.state),
        type=JobType(job.type),
        started_at=job.started_at,
        finished_at=job.finished_at,
        name=job.name,
        results=[result_mapper.dataclass_to_dto(result) for result in job.results],
    )


def dataclass_to_simple(job: JobDataclass) -> SimpleJobDto:
    return SimpleJobDto(
        id=job.id,
        deployment_id=job.deployment_id,
        name=job.name,
        state=JobState(job.state),
    )
