"""Module containing the routes of the Taskmanager API."""

from qunicorn_core.celery import CELERY
from ..models.jobs import JobIDSchema
from ..models.jobs import JobRegisterSchema
from typing import Dict
from flask.helpers import url_for
from flask.views import MethodView
from dataclasses import dataclass
from http import HTTPStatus
from . import register_job
import time

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


@CELERY.task()
def createJob():
    print("Job Registered")
    time.sleep(5)
    print("Job complete")
    return 0


@JOBMANAGER_API.route("/")
class JobIDView(MethodView):
    """Jobs endpoint for collection of all jobs."""

    @JOBMANAGER_API.response(HTTPStatus.OK, JobIDSchema())
    def get(self):
        """Get registered job list."""
        return [
            JobID(
                id=url_for("jobmanager-api.JobIDView", _external=True),
                description="Placeholder for Jobs",
                taskmode=0,
            )
        ]

    @JOBMANAGER_API.arguments(JobRegisterSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, JobIDSchema())
    def post(self, new_job_data: dict):
        """Create/Register new job."""
        createJob.delay()
        
        pass


@JOBMANAGER_API.route("/<string:job_id>/")
class JobDetailView(MethodView):
    """Jobs endpoint for a single job."""

    @JOBMANAGER_API.response(HTTPStatus.OK, JobIDSchema())
    def get(self, job_id: str):
        """Get the urls for the jobmanager api for job control."""
        
        pass

    @JOBMANAGER_API.arguments(JobRegisterSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, JobIDSchema())
    def post(self, job_id: str):
        """Cancel a job execution via id."""
  
        pass

    
    @JOBMANAGER_API.arguments(JobRegisterSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, JobIDSchema())
    def delete(self, job_id: str):
        """Delete job data via id."""
       
        pass

        
    @JOBMANAGER_API.arguments(JobRegisterSchema(), location="json")
    @JOBMANAGER_API.response(HTTPStatus.OK, JobIDSchema())
    def put(self, job_id: str):
        """Pause a job via id."""
       
        pass


  