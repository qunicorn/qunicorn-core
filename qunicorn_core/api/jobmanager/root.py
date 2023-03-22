"""Module containing the root endpoint of the JobMANAGER API."""

from dataclasses import dataclass
from flask.helpers import url_for
from flask.views import MethodView
from http import HTTPStatus
from ..util import SecurityBlueprint as SmorestBlueprint
from ..models import RootSchema


JOBMANAGER_API = SmorestBlueprint(
    "jobmanager-api",
    "JOBMANAGER API",
    description="Jobmanager API for the control plane.",
    url_prefix="/jobs/",
)


@dataclass()
class RootData:
    root: str
