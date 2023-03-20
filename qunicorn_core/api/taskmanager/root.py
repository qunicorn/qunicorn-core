"""Module containing the root endpoint of the TASKMANAGER API."""

from dataclasses import dataclass
from flask.helpers import url_for
from flask.views import MethodView
from http import HTTPStatus
from ..util import SecurityBlueprint as SmorestBlueprint
from ..models import RootSchema


# TASKMANAGER_API = SmorestBlueprint(
#    "taskmanager-api", "TASKMANAGER API", description="Taskmanager API for the control plane.", url_prefix="/taskmanager"
# )

TASKMANAGER_API = SmorestBlueprint(
    "taskmanager-api",
    "TASKMANAGER API",
    description="Taskmanager API for the control plane.",
)


@dataclass()
class RootData:
    root: str


@TASKMANAGER_API.route("/task/")
class RootView(MethodView):
    """Root endpoint of the taskmanager api."""

    @TASKMANAGER_API.response(HTTPStatus.OK, RootSchema())
    def get(self):
        """Get the urls of the next endpoints of the taskmanager api to call."""
        return RootData(root=url_for("taskmanager-api.TaskIDView", _external=True))
