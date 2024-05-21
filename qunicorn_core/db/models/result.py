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

from typing import Any, Optional, Dict

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import sqltypes as sql

from . import job as job_model
from . import quantum_program
from .db_model import DbModel
from ..db import REGISTRY
from ...static.enums.result_type import ResultType


@REGISTRY.mapped_as_dataclass
class ResultDataclass(DbModel):
    """Dataclass for storing results of a job

    Attributes:
        id (int): The ID of the result. (set by the database)
        job (JobDataclass, optional): The job that was executed.
        program (QuantumProgramDataclass, optional): The specific program that was executed.
        data (Any): The result of the job, in the given result_type.
        meta (dict): Some other data that was given by ibm.
        result_type (Enum): Result type depending on the Job_Type of the job.
    """

    # non-default arguments
    id: Mapped[int] = mapped_column(sql.INTEGER(), primary_key=True, autoincrement=True, init=False)
    # default arguments
    job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("Job.id", ondelete="CASCADE"), default=None, nullable=True, init=False
    )
    job: Mapped[Optional["job_model.JobDataclass"]] = relationship(
        lambda: job_model.JobDataclass, back_populates="results", lazy="selectin", default=None
    )
    program_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("QuantumProgram.id", ondelete="CASCADE"), default=None, nullable=True, init=False
    )
    program: Mapped[Optional["quantum_program.QuantumProgramDataclass"]] = relationship(
        lambda: quantum_program.QuantumProgramDataclass, lazy="selectin", default=None
    )
    data: Mapped[Any] = mapped_column(sql.JSON, default=None, nullable=True)
    meta: Mapped[Dict[str, Any]] = mapped_column(sql.JSON, default=None, nullable=True)
    result_type: Mapped[str] = mapped_column(sql.String(50), default=ResultType.COUNTS.value)
