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


"""Module containing all Dtos and their Schemas  for tasks in the Services API."""
from dataclasses import dataclass

from flask import url_for, current_app
import marshmallow as ma

from ..flask_api_utils import MaBaseSchema
from ...static.enums.assembler_languages import AssemblerLanguage

__all__ = ["ProviderDtoSchema", "ProviderIDSchema", "ProviderDto", "ProviderFilterParamsSchema"]


@dataclass
class ProviderDto:
    id: int
    with_token: bool
    supported_languages: list[AssemblerLanguage]
    name: str


class ProviderDtoSchema(MaBaseSchema):
    id = ma.fields.Integer(required=True, allow_none=False)
    with_token = ma.fields.Boolean(required=False, allow_none=True)
    supported_languages = ma.fields.List(ma.fields.Enum(required=True, allow_none=False, enum=AssemblerLanguage))
    name = ma.fields.Str(required=True, allow_none=False)
    qprov_link = ma.fields.Function(lambda obj: create_qprov_provider_link(obj))
    self = ma.fields.Function(lambda obj: url_for("provider-api.ProviderIDView", provider_id=obj.id))
    devices = ma.fields.Function(lambda obj: url_for("device-api.DeviceView", provider=obj.id))


class ProviderIDSchema(MaBaseSchema):
    provider_id = ma.fields.String(required=True, allow_none=False)


class ProviderFilterParamsSchema(MaBaseSchema):
    name = ma.fields.String(
        required=False,
        missing=None,
        load_only=True,
        description="Use % as wildcard and \\ to escape a % wildcard.",
    )


def create_qprov_provider_link(provider: ProviderDto):
    from ...db.models.provider import ProviderDataclass

    qprov_id = ProviderDataclass.get_by_id_or_404(provider.id).qprov_id

    if qprov_id is None:
        return ma.missing

    qprov_root_url = current_app.config.get("QPROV_URL")

    if qprov_root_url is None:
        return ma.missing

    qprov_link = f"{qprov_root_url}/qprov/providers/{qprov_id}"

    return qprov_link
