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

from typing import Optional, Sequence, List, Union

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import sqltypes as sql
from sqlalchemy.sql import sqltypes as sql
from sqlalchemy.sql.expression import select
from sqlalchemy.sql.schema import ForeignKey
from .deployments import DeploymentDataclass

from ..db import MODEL, REGISTRY

from datetime import datetime


@REGISTRY.mapped_as_dataclass
class JobDataclass:
    """Dataclass for storing Jobdata
    
    Attributes:
        job_id (int): automatically generated database id. Use the id to fetch this information from the database.
        job_name (str, optional): Optional name for a job
        user_id (str): A user_id associated to the job
        deployment_id (int): A deployment_id associated with the job
        started_at (datetime, optional): the moment the job was scheduled. (default :py:func:`~datetime.datetime.utcnow`)
        finished_at (Optional[datetime], optional): the moment the job finished successfully or with an error.
        parameters (str): the parameters for the Job. Job parameters should already be prepared and error checked before starting the task.
        data (Union[dict, list, str, float, int, bool, None]): mutable JSON-like store for additional lightweight task data. Default value is empty dict.
        task_status (Optional[str], optional): the status of a job, can only be ``PENDING``, ``RUNNING`` ,``FINISHED``, or ``ERROR``.
        results (List[Job], optional): the output data (files) of the job
    """


    job_id: Mapped[int] = mapped_column(sql.INTEGER(), primary_key=True, init=False)
    job_name: Mapped[Optional[str]] = mapped_column(sql.String(50), default=None)
    started_at: Mapped[datetime] = mapped_column(
        sql.TIMESTAMP(timezone=True), default=datetime.utcnow()
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        sql.TIMESTAMP(timezone=True), default=None, nullable=True
    )
    user_id: Mapped[str] = mapped_column(sql.String(50))
    deployment_id: Mapped[int] = mapped_column(ForeignKey("DeploymentDataclass.deployment_id"))

    __tablename__ = "Jobs"
