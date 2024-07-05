# Copyright 2023 University of Stuttgart.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import traceback
from datetime import datetime, timezone
from typing import List, Optional, Union, Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import Select, or_, select
from sqlalchemy.sql import sqltypes as sql

from . import deployment as deployment_model
from . import quantum_program
from .db_model import DbModel, T
from .device import DeviceDataclass
from .result import ResultDataclass
from .job_state import TransientJobStateDataclass
from ..db import DB, REGISTRY
from ...static.enums.job_state import JobState
from ...static.enums.result_type import ResultType


@REGISTRY.mapped_as_dataclass
class JobDataclass(DbModel):
    """Dataclass for storing Jobs

    Attributes:
        id (int): The id of a job. (set by the database)
        name (str, optional): Optional name for a job.
        results (List[ResultDataclass], optional): List of results for each quantum program that was executed.
        executed_by(str): A user_id associated to the job, user that wants to execute the job.
        executed_on (DeviceDataclass|None): The device where the job is running on.
        deployment (DeploymentDataclass|None): The deployment where the program is coming from.
        progress (float): The progress of the job.
        state (str): The state of a job, enum JobState.
        shots (int): The number of shots for the job
        type (JobType): The type of the job.
        started_at (datetime, optional): The moment the job was scheduled. (default: datetime.utcnow)
        provider_specific_id (str, optional): The provider specific id for the job. (Used for canceling)
        celery_id (str, optional): The celery id for the job. (Used for canceling)
        finished_at (Optional[datetime], optional): The moment the job finished successfully or with an error.
    """

    # non-default arguments
    id: Mapped[int] = mapped_column(sql.INTEGER(), primary_key=True, autoincrement=True, init=False)
    name: Mapped[Optional[str]] = mapped_column(sql.String(50))
    executed_by: Mapped[Optional[str]] = mapped_column(sql.String(100))
    executed_on: Mapped[Optional[DeviceDataclass]] = relationship(DeviceDataclass, lazy="selectin")
    deployment: Mapped[Optional["deployment_model.DeploymentDataclass"]] = relationship(
        lambda: deployment_model.DeploymentDataclass, back_populates="jobs", lazy="selectin", cascade="save-update"
    )
    progress: Mapped[int] = mapped_column(sql.INTEGER())
    state: Mapped[str] = mapped_column(sql.String(50))
    shots: Mapped[int] = mapped_column(sql.INTEGER())
    type: Mapped[str] = mapped_column(sql.String(50))
    # default arguments
    started_at: Mapped[datetime] = mapped_column(
        sql.TIMESTAMP(timezone=True), default_factory=lambda: datetime.now(timezone.utc)
    )
    provider_specific_id: Mapped[Optional[str]] = mapped_column(sql.String(50), nullable=True, default=None)
    celery_id: Mapped[Optional[str]] = mapped_column(sql.String(50), nullable=True, default=None)
    executed_on_id: Mapped[int] = mapped_column(
        ForeignKey(DeviceDataclass.id, ondelete="SET NULL"), default=None, nullable=True, init=False
    )
    deployment_id: Mapped[int] = mapped_column(
        ForeignKey("Deployment.id", ondelete="SET NULL"), default=None, nullable=True, init=False
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(sql.TIMESTAMP(timezone=True), default=None, nullable=True)
    results: Mapped[List[ResultDataclass]] = relationship(
        ResultDataclass, back_populates="job", lazy="selectin", default_factory=list
    )

    _transient: Mapped[List[TransientJobStateDataclass]] = relationship(
        TransientJobStateDataclass, back_populates="job", lazy="selectin", default_factory=list
    )

    @classmethod
    def apply_authentication_filter(cls, query: Select[T], user_id: Optional[str]) -> Select[T]:
        if user_id is None:
            return query.where(cls.executed_by == None)  # noqa: E711
        return query.where(or_(cls.executed_by == None, cls.executed_by == user_id))  # noqa: E711

    @classmethod
    def get_by_deployment(cls, deployment: Union[int, "deployment_model.DeploymentDataclass"]):
        q = select(cls)
        if isinstance(deployment, int):
            q = q.where(cls.deployment_id == deployment)
        elif isinstance(deployment, deployment_model.DeploymentDataclass):
            q = q.where(cls.deployment == deployment)
        return DB.session.execute(q).scalars().all()

    @classmethod
    def get_by_deployment_authenticated(
        cls, deployment: Union[int, "deployment_model.DeploymentDataclass"], user_id: Optional[str]
    ):
        q = cls.apply_authentication_filter(select(cls), user_id)
        if isinstance(deployment, int):
            q = q.where(cls.deployment_id == deployment)
        elif isinstance(deployment, deployment_model.DeploymentDataclass):
            q = q.where(cls.deployment == deployment)
        return DB.session.execute(q).scalars().all()

    def get_transient_state(self, key: str, default: Optional[Any] = ..., *, program: Optional[int] = None):
        for state in self._transient:
            if state.program_id == program:
                if isinstance(state.data, dict) and key in state.data:
                    return state.data[key]
        if default == ...:
            raise KeyError(f"Key '{key}' not found in transient job state!")
        return default

    def save_results(self, results: List[ResultDataclass], job_state: Union[JobState, str] = JobState.FINISHED):
        """Update the job to include the results and commit everything to the database."""
        self.finished_at = datetime.now(timezone.utc)
        self.progress = 100
        self.results = results
        self.state = job_state.value if isinstance(job_state, JobState) else job_state
        for result in results:
            result.save()  # add nested objects to db session
        self.save(commit=True)

    def save_error(self, exception: BaseException, program: Optional["quantum_program.QuantumProgramDataclass"] = None):
        exception_message: str = str(exception)
        stack_trace: str = "".join(traceback.format_exception(exception))

        error_result = ResultDataclass(
            result_type=ResultType.ERROR.value,
            job=self,
            program=program,
            data={"exception_message": exception_message},
            meta={"stack_trace": stack_trace},
        )
        self.results.append(error_result)

        if self.finished_at is None:
            self.finished_at = datetime.now(timezone.utc)
        self.progress = 100
        self.state = JobState.ERROR.value

        error_result.save()
        self.save(commit=True)
