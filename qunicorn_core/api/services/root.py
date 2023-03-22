"""Module containing the root endpoint of the DEVICES API."""

from dataclasses import dataclass
from flask.helpers import url_for
from flask.views import MethodView
from http import HTTPStatus
from ..util import SecurityBlueprint as SmorestBlueprint
from ..models import RootSchema


SERVICES_API = SmorestBlueprint(
    "services-api",
    "SERVICES API",
    description="Services API to list available resources.",
    url_prefix="/services",
)


@dataclass()
class RootData:
    root: str


@SERVICES_API.route("/")
class RootView(MethodView):
    """Root endpoint of the services api, to list all available services."""

    @SERVICES_API.response(HTTPStatus.OK, RootSchema())
    def get(self):
        """Get the urls of the next endpoints of the devices api to call."""
        return RootData(root=url_for("services-api.ServicesView", _external=True))
