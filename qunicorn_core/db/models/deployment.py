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

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import or_
from sqlalchemy.sql import sqltypes as sql

from . import job
from .db_model import DbModel, T
from .quantum_program import QuantumProgramDataclass
from ..db import REGISTRY


@REGISTRY.mapped_as_dataclass
class DeploymentDataclass(DbModel):
    """Dataclass for storing deployments

    Attributes:
        id (int): The id of a deployment. (set by the database)
        name (str, optional): Optional name for a deployment.
        deployed_at (Date): Date of the creation of a deployment. (defaults to current time)
        programs (List[QuantumProgramDataclass]): A list of quantum programs.
        deployed_by (str): The  user_id that deployed this Deployment.
    """

    # non-default arguments
    id: Mapped[int] = mapped_column(sql.INTEGER(), primary_key=True, autoincrement=True, init=False)
    name: Mapped[Optional[str]] = mapped_column(sql.String(50))
    # default arguments
    deployed_at: Mapped[datetime] = mapped_column(
        sql.TIMESTAMP(timezone=True), default_factory=lambda: datetime.now(timezone.utc)
    )
    programs: Mapped[List[QuantumProgramDataclass]] = relationship(
        QuantumProgramDataclass,
        back_populates="deployment",
        lazy="selectin",
        cascade="all, delete-orphan",
        default_factory=list,
    )
    deployed_by: Mapped[Optional[str]] = mapped_column(sql.String(100), nullable=True, default=None)

    jobs: Mapped[List["job.JobDataclass"]] = relationship(
        lambda: job.JobDataclass, back_populates="deployment", lazy="select", default_factory=list, init=False
    )

    @classmethod
    def apply_authentication_filter(cls, query: Select[T], user_id: Optional[str]) -> Select[T]:
        if user_id is None:
            return query.where(cls.deployed_by == None)
        return query.where(or_(cls.deployed_by == None, cls.deployed_by == user_id))
