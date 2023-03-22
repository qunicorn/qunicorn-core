"""Module containing the routes of the Taskmanager API."""

from ..models.jobs import JobIDSchema
from ..models.jobs import JobRegisterSchema
from typing import Dict
from flask.helpers import url_for
from flask.views import MethodView
from dataclasses import dataclass
from http import HTTPStatus

from .root import JOBMANAGER_API


@dataclass
class JobID:
    id: str
    description: str
    taskmode: int


@dataclass
class JobRegister:
    circuit: str
    provider: str
    qpu: str
    credentials: dict
    shots: int
    circuit_format: str


@JOBMANAGER_API.route("/")
class JobIDView(MethodView):
    """Tasks endpoint for collection of all tasks."""

    @JOBMANAGER_API.response(HTTPStatus.OK, JobIDSchema())
    def get(self):
        """Get registered task list."""
        return [
            JobID(
                id=url_for("jobmanager-api.JobIDView", _external=True),
                description="Placeholder for Tasks",
                taskmode=0,
            )
        ]

    @JOBMANAGER_API.arguments(JobRegisterSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, JobIDSchema())
    def post(self, new_task_data: dict):
        """Create/Register new task."""
        return JobRegister(
            circuit='OPENQASM 2.0; include "qelib1.inc"; qreg q[4]; creg c[4];x q[0]; x q[2];barrier q;h q[0];cu1(pi/2) q[1],q[0];h q[1];cu1(pi/4) q[2],q[0];cu1(pi/2) q[2],q[1];h q[2];cu1(pi/8) q[3],q[0];cu1(pi/4) q[3],q[1];cu1(pi/2) q[3],q[2];h q[3];measure q -> c;',
            provider="IBM",
            qpu="aer_qasm_simulator",
            credentials={"token": "YOUR TOKEN"},
            shots=1000,
            circuit_format="openqasm2",
        )


@JOBMANAGER_API.route("/<string:job_id>/")
class JObDetailView(MethodView):
    """Tasks endpoint for a single task."""

    @JOBMANAGER_API.response(HTTPStatus.OK, JobIDSchema())
    def get(self, job_id: str):
        """Get the urls for the taskmanager api for tasks control."""
        return JobID(  # return task
            id=url_for("jobmanager-api.JobIDView", _external=True),
            description="Placeholder for Jobs",
            taskmode=0,
        )
