"""Module containing the root endpoint of the DEPLOYMENT API."""

from dataclasses import dataclass
from flask.helpers import url_for
from flask.views import MethodView
from http import HTTPStatus
from ..util import SecurityBlueprint as SmorestBlueprint
from ..models import RootSchema


DEPLOYMENT_API = SmorestBlueprint(
    "deployment-api",
    "DEPLOYMENT API",
    description="Deployment API for the control plane.",
    url_prefix="/deployment/",
)


@dataclass()
class RootData:
    root: str
