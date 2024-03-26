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

from qunicorn_core.api.api_models import DeviceDto
from qunicorn_core.api.api_models.device_dtos import SimpleDeviceDto
from qunicorn_core.core.mapper import provider_mapper
from qunicorn_core.db.models.device import DeviceDataclass
from qunicorn_core.db.models.provider import ProviderDataclass


def dto_to_dataclass(device: DeviceDto, provider: ProviderDataclass) -> DeviceDataclass:
    return DeviceDataclass(
        name=device.name,
        is_local=device.is_local,
        is_simulator=device.is_simulator,
        num_qubits=device.num_qubits,
        provider=provider,
    )


def dataclass_to_dto(device: DeviceDataclass) -> DeviceDto:
    return DeviceDto(
        id=device.id,
        name=device.name,
        is_local=device.is_local,
        is_simulator=device.is_simulator,
        num_qubits=device.num_qubits,
        provider=provider_mapper.dataclass_to_dto(device.provider),
    )


def dataclass_to_simple(device: DeviceDataclass) -> SimpleDeviceDto:
    return SimpleDeviceDto(
        device_id=device.id,
        device_name=device.name,
        provider_name=device.provider.name,
    )
