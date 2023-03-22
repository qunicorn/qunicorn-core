"""Module containing the routes of the Taskmanager API."""

from ..models.devices import DevicesSchema, DeviceIDSchema
from typing import Dict, List
from flask.helpers import url_for
from flask.views import MethodView
from dataclasses import dataclass
from http import HTTPStatus

from .root import DEVICES_API


@dataclass
class DEVICES:
    serviceType: str
    description: str
    address: str
    status: str
    name: str
    url: str
    simulator: bool



@DEVICES_API.route("/<string:device_id>/")
class DevicesView(MethodView):
    """Devices Endpoint to get properties of a specific device/service."""

    @DEVICES_API.arguments(DeviceIDSchema(), location="path")
    @DEVICES_API.response(HTTPStatus.OK, DevicesSchema())
    def get(self):
        """Test for devices/service list."""
        
        pass


@DEVICES_API.route("/<string:device_id>/status")
class DevicesView(MethodView):
    """Devices Endpoint to get properties of a specific device/service."""

    @DEVICES_API.arguments(DeviceIDSchema(), location="path")
    @DEVICES_API.response(HTTPStatus.OK, DevicesSchema())
    def get(self):
        """Get detailed information about a specific device."""
    
        pass


@DEVICES_API.route("/<string:device_id>/calibration")
class DevicesView(MethodView):
    """Devices Endpoint to get properties of a specific device/service."""

    @DEVICES_API.arguments(DeviceIDSchema(), location="path")
    @DEVICES_API.response(HTTPStatus.OK, DevicesSchema())
    def get(self):
        """Get calibration data for a specific device in a uniform way."""

        pass


@DEVICES_API.route("/<string:device_id>/jobs")
class DevicesView(MethodView):
    """Devices Endpoint to get properties of a specific device/service."""

    @DEVICES_API.response(HTTPStatus.OK, DevicesSchema())
    def get(self):
        """Test for devices/service list."""
        
        pass

