"""Module containing the root endpoint of the DEVICES API."""

from dataclasses import dataclass
from flask.helpers import url_for
from flask.views import MethodView
from http import HTTPStatus
from ..util import SecurityBlueprint as SmorestBlueprint
from ..models import RootSchema


DEVICES_API = SmorestBlueprint(
    "devices-api",
    "DEVICES API",
    description="Devices API to list available resources.",
    url_prefix="/devices",
)


@dataclass()
class RootData:
    root: str


@DEVICES_API.route("/")
class RootView(MethodView):
    """Root endpoint of the devices api, to list all available devices/services."""

    @DEVICES_API.response(HTTPStatus.OK, RootSchema())
    def get(self):
        """Get the urls of the next endpoints of the devices api to call."""
        return RootData(root=url_for("devices-api.DevicesView", _external=True))
