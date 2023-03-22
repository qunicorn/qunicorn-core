"""Module containing the routes of the Taskmanager API."""

from ..models.services import ServicesSchema, ServiceIDSchema
from typing import Dict, List
from flask.helpers import url_for
from flask.views import MethodView
from dataclasses import dataclass
from http import HTTPStatus

from .root import SERVICES_API


@dataclass
class SERVICES:
    serviceType: str
    description: str
    address: str
    status: str
    name: str
    url: str
    simulator: bool


@SERVICES_API.route("/<string:service_id>/")
class ServicesView(MethodView):
    """Services Endpoint to get properties of a specific service."""

    @SERVICES_API.arguments(HTTPStatus.OK, ServiceIDSchema())
    @SERVICES_API.response(HTTPStatus.OK, ServicesSchema())
    def get(self):
        """Test for devices/service list."""
        
        pass

