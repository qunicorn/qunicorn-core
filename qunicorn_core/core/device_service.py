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

from qunicorn_core.api.api_models.device_dtos import (
    DeviceDto,
    DeviceRequestDto,
    SimpleDeviceDto,
)
from qunicorn_core.core.mapper import device_mapper
from qunicorn_core.core.pilotmanager import pilot_manager
from qunicorn_core.db.models.device import DeviceDataclass
from qunicorn_core.util import logging


def update_devices(device_request: DeviceRequestDto) -> list[SimpleDeviceDto]:
    """Update all backends for the provider from device_request"""
    logging.info(f"Update all available devices for {device_request.provider_name} in database.")
    pilot_manager.update_devices_from_provider(device_request)
    return [device_mapper.dataclass_to_simple(device) for device in DeviceDataclass.get_all()]


def get_all_devices() -> list[SimpleDeviceDto]:
    """Gets all Devices from the DB and maps them"""
    return [device_mapper.dataclass_to_simple(device) for device in DeviceDataclass.get_all()]


def get_device_by_id(device_id: int) -> DeviceDto:
    """Gets a Device from the DB by its ID and maps it"""
    return device_mapper.dataclass_to_dto(DeviceDataclass.get_by_id_or_404(device_id))


def check_if_device_available(device_id: int, token: Optional[str]) -> dict:
    """Checks if the backend is available at the provider currently"""
    device: DeviceDto = get_device_by_id(device_id)
    if pilot_manager.check_if_device_available_from_provider(device, token):
        return {"available": True}
    return {"available": False}


def get_device_data_from_provider(device_id: int, token: str) -> dict:
    """Get the device from the provider and return the configuration as dict"""
    device: DeviceDto = get_device_by_id(device_id)

    return pilot_manager.get_device_data_from_provider(device, token)
