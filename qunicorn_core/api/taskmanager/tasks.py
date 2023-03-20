"""Module containing the routes of the Taskmanager API."""

from ..models.tasks import TaskIDSchema
from ..models.tasks import TaskRegisterSchema
from typing import Dict
from flask.helpers import url_for
from flask.views import MethodView
from dataclasses import dataclass
from http import HTTPStatus

from .root import TASKMANAGER_API


@dataclass
class TaskID:
    id: str
    description: str
    taskmode: int


@dataclass
class TaskRegister:
    circuit: str
    provider: str
    qpu: str
    credentials: dict
    shots: int
    circuit_format: str


@TASKMANAGER_API.route("/")
class TaskIDView(MethodView):
    """Tasks endpoint for collection of all tasks."""

    @TASKMANAGER_API.response(HTTPStatus.OK, TaskIDSchema())
    def get(self):
        """Get registered task list."""
        return [
            TaskID(
                id=url_for("taskmanager-api.TaskIDView", _external=True),
                description="Placeholder for Tasks",
                taskmode=0,
            )
        ]

    @TASKMANAGER_API.arguments(TaskRegisterSchema(), location="json")
    @TASKMANAGER_API.response(HTTPStatus.OK, TaskIDSchema())
    def post(self, new_task_data: dict):
        """Create/Register new task."""
        return TaskRegister(
            circuit='OPENQASM 2.0; include "qelib1.inc"; qreg q[4]; creg c[4];x q[0]; x q[2];barrier q;h q[0];cu1(pi/2) q[1],q[0];h q[1];cu1(pi/4) q[2],q[0];cu1(pi/2) q[2],q[1];h q[2];cu1(pi/8) q[3],q[0];cu1(pi/4) q[3],q[1];cu1(pi/2) q[3],q[2];h q[3];measure q -> c;',
            provider="IBM",
            qpu="aer_qasm_simulator",
            credentials={"token": "YOUR TOKEN"},
            shots=1000,
            circuit_format="openqasm2",
        )


@TASKMANAGER_API.route("/<string:task_id>/")
class TaskDetailView(MethodView):
    """Tasks endpoint for a single task."""

    @TASKMANAGER_API.response(HTTPStatus.OK, TaskIDSchema())
    def get(self, task_id: str):
        """Get the urls for the taskmanager api for tasks control."""
        return TaskID(  # return task
            id=url_for("taskmanager-api.TaskIDView", _external=True),
            description="Placeholder for Tasks",
            taskmode=0,
        )
