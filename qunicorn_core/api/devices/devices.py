"""Module containing the routes of the Taskmanager API."""

from ..models.devices import DevicesSchema
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


#@DEVICES_API.route("/<string:service_name>/")
@DEVICES_API.route("/test")
class DevicesView(MethodView):
    """Devices Endpoint to get properties of a specific device/service."""

    @DEVICES_API.response(HTTPStatus.OK, DevicesSchema())
    def get(self):
        """Test for devices/service list."""
        return DEVICES(
            services_type="all",
            name = "name",
            description="",
            address="",
            status="",
            url="",
            simulator=True,
        )
