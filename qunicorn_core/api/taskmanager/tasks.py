"""Module containing the authentication API of the v1 API."""

from ..models.tasks import TaskIDSchema
from typing import Dict
from flask.helpers import url_for
from flask.views import MethodView
from dataclasses import dataclass
from http import HTTPStatus
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    current_user,
)

from .root import TASKMANAGER_API
from ..jwt import DemoUser


@dataclass
class TaskID:
    id: str
    description: str


@TASKMANAGER_API.route("/tasks/")
class TaskIDView(MethodView):
    """Tasks endpoint for all tasks."""

    @TASKMANAGER_API.response(HTTPStatus.OK, TaskIDSchema())
    def get(self):
        """Get the urls for the taskmanager api for tasks control."""
        return TaskID(
            id=url_for("taskmanager-api.TaskIDView", _external=True),
            description="Placeholder for Tasks",
        )