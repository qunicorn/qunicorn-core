"""Module containing the authentication API of the v1 API."""

from ..models.tasks import TaskIDSchema
from ..models.tasks import TaskRegisterSchema
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
    taskmode: int


@dataclass
class TaskRegister:
    circuit: str
    provider: str
    qpu: str
    credentials: dict
    shots: int
    circuit_format: str


@TASKMANAGER_API.route("/tasks/")
class TaskIDView(MethodView):
    """Tasks endpoint for all tasks."""

    @TASKMANAGER_API.response(HTTPStatus.OK, TaskIDSchema())
    def get(self):
        """Get the urls for the taskmanager api for tasks control."""
        return TaskID(
            id=url_for("taskmanager-api.TaskIDView", _external=True),
            description="Placeholder for Tasks",
            taskmode=0,
        )


@TASKMANAGER_API.route("/tasks/register")
class TaskRegisterView(MethodView):
    """Tasks endpoint for register tasks."""

    @TASKMANAGER_API.response(HTTPStatus.OK, TaskRegisterSchema())
    def get(self):
        """Get the inputs for the taskmanager api for register."""
        return TaskRegister(
            circuit='OPENQASM 2.0; include "qelib1.inc"; qreg q[4]; creg c[4];x q[0]; x q[2];barrier q;h q[0];cu1(pi/2) q[1],q[0];h q[1];cu1(pi/4) q[2],q[0];cu1(pi/2) q[2],q[1];h q[2];cu1(pi/8) q[3],q[0];cu1(pi/4) q[3],q[1];cu1(pi/2) q[3],q[2];h q[3];measure q -> c;',
            provider="IBM",
            qpu="aer_qasm_simulator",
            credentials={"token": "YOUR TOKEN"},
            shots=1000,
            circuit_format="openqasm2",
        )
