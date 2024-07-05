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
from typing import Optional

from qunicorn_core.api.api_models.provider_dtos import ProviderDto
from qunicorn_core.core.mapper import provider_mapper
from qunicorn_core.db.models.provider import ProviderDataclass


def get_all_providers(name: Optional[str] = None) -> list[ProviderDto]:
    """Gets all Providers from the DB and maps them"""
    where = []
    if name:
        if "%" in name:
            where.append(ProviderDataclass.name.like(name, escape="\\"))
        else:
            where.append(ProviderDataclass.name == name)
    return [provider_mapper.dataclass_to_dto(provider) for provider in ProviderDataclass.get_all(where=where)]


def get_provider_by_id(provider_id: int) -> ProviderDto:
    """Gets a Provider from the DB by its ID and maps it"""
    return provider_mapper.dataclass_to_dto(ProviderDataclass.get_by_id_or_404(provider_id))
