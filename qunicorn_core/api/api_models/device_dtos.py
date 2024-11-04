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


"""Module containing all Dtos and their Schemas for tasks in the Devices API."""
from dataclasses import dataclass

from flask import url_for, current_app
import marshmallow as ma
from marshmallow.validate import OneOf

from qunicorn_core.api.api_models.provider_dtos import ProviderDto, ProviderDtoSchema
from qunicorn_core.api.flask_api_utils import MaBaseSchema

from qunicorn_core.static.enums.provider_name import ProviderName

__all__ = [
    "DeviceDtoSchema",
    "SimpleDeviceDtoSchema",
    "SimpleDeviceDto",
    "DeviceDto",
    "DeviceRequestDtoSchema",
    "ApiTokenHeaderSchema",
    "DeviceFilterParamsSchema",
    "DeviceUpdateFilterParamsSchema",
    "DeviceStatusResponseSchema",
]


@dataclass
class DeviceDto:
    id: int
    name: str
    num_qubits: int
    is_simulator: bool
    is_local: bool
    provider: ProviderDto | None = None


class DeviceDtoSchema(MaBaseSchema):
    id = ma.fields.Integer(required=True, allow_none=False, metadata={"description": "The unique deviceID."})
    name = ma.fields.String(required=True, allow_none=False, metadata={"description": "The name of the device."})
    num_qubits = ma.fields.Integer(required=True, allow_none=False)
    is_simulator = ma.fields.Boolean(required=True, allow_none=False)
    is_local = ma.fields.Boolean(required=True, allow_none=False)
    provider = ma.fields.Nested(ProviderDtoSchema())
    qprov_link = ma.fields.Function(lambda obj: create_qprov_device_link(obj))
    self = ma.fields.Function(lambda obj: url_for("device-api.DeviceIdView", device_id=obj.id))


class DeviceRequestDtoSchema(MaBaseSchema):
    token = ma.fields.String(required=False, metadata={"example": ""})


class ApiTokenHeaderSchema(MaBaseSchema):
    token = ma.fields.String(required=False, data_key="X_QUNICORN_PROVIDER_TOKEN", metadata={"example": ""})


@dataclass
class SimpleDeviceDto:
    id: int
    device_name: str
    provider_name: str


class SimpleDeviceDtoSchema(MaBaseSchema):
    id = ma.fields.Integer(required=True, dump_only=True)
    device_name = ma.fields.String(required=True, dump_only=True)
    provider_name = ma.fields.String(required=True, dump_only=True, validate=OneOf([p.value for p in ProviderName]))
    self = ma.fields.Function(lambda obj: url_for("device-api.DeviceIdView", device_id=obj.id))


class DeviceFilterParamsSchema(MaBaseSchema):
    provider = ma.fields.Integer(required=False, missing=None, load_only=True)
    min_qubits = ma.fields.Integer(data_key="min-qubits", required=False, missing=None, load_only=True)
    is_simulator = ma.fields.Boolean(data_key="is-simulator", required=False, missing=None, load_only=True)
    is_local = ma.fields.Boolean(data_key="is-local", required=False, missing=None, load_only=True)


class DeviceUpdateFilterParamsSchema(MaBaseSchema):
    provider = ma.fields.Integer(required=True, load_only=True)


class DeviceStatusResponseSchema(MaBaseSchema):
    available = ma.fields.Bool(dump_only=True)


def create_qprov_device_link(device: DeviceDto):
    from qunicorn_core.db.models.device import DeviceDataclass
    from qunicorn_core.db.models.provider import ProviderDataclass

    provider_qprov_id = ProviderDataclass.get_by_id_or_404(device.provider.id).qprov_id

    if provider_qprov_id is None:
        return ma.missing

    device_qprov_id = DeviceDataclass.get_by_id_or_404(device.id).qprov_id

    if device_qprov_id is None:
        return ma.missing

    qprov_root_url = current_app.config.get("QPROV_URL")

    if qprov_root_url is None:
        return ma.missing

    qprov_link = f"{qprov_root_url}/providers/{provider_qprov_id}/qpus/{device_qprov_id}"

    return qprov_link
