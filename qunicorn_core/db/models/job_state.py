# Copyright 2024 University of Stuttgart.
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

from typing import Any, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import sqltypes as sql

from . import job as job_model
from . import quantum_program
from .db_model import DbModel
from ..db import REGISTRY


@REGISTRY.mapped_as_dataclass
class TransientJobStateDataclass(DbModel):
    """A table for storing transient data during job execution.

    Data in this table is expected to only live as long as the job is considered RUNNING.
    Any data of finished, cancelled or errored jobs may be deleted at any time.
    However, pilots should actively delete transient data when a job is finished.

    Transient data can be stored for the job, or a specific program part of a job.
    """

    id: Mapped[int] = mapped_column(sql.INTEGER(), primary_key=True, autoincrement=True, init=False)
    job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("Job.id", ondelete="CASCADE"), default=None, nullable=False, init=False
    )
    job: Mapped["job_model.JobDataclass"] = relationship(
        lambda: job_model.JobDataclass, back_populates="_transient", lazy="selectin", default=None
    )
    program_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("QuantumProgram.id", ondelete="CASCADE"), default=None, nullable=True, init=False
    )
    program: Mapped[Optional["quantum_program.QuantumProgramDataclass"]] = relationship(
        lambda: quantum_program.QuantumProgramDataclass, lazy="selectin", default=None
    )
    circuit_fragment_id: Mapped[Optional[int]] = mapped_column(sql.INTEGER(), nullable=True, default=None)
    data: Mapped[Any] = mapped_column(sql.JSON, default=None, nullable=True)
