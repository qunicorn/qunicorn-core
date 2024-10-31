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
from qunicorn_core.api.api_models import DeploymentDto
from qunicorn_core.core.mapper import quantum_program_mapper
from qunicorn_core.db.models.deployment import DeploymentDataclass


def dataclass_to_dto(deployment: DeploymentDataclass) -> DeploymentDto:
    return DeploymentDto(
        id=deployment.id,
        name=deployment.name,
        deployed_by=deployment.deployed_by,
        deployed_at=deployment.deployed_at,
        programs=[quantum_program_mapper.dataclass_to_dto(qc) for qc in deployment.programs],
    )
