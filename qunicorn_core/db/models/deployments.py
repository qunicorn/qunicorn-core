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

from ..db import MODEL, REGISTRY

@REGISTRY.mapped_as_dataclass
class DeploymentDataclass:
    """Dataclass for storing deployment data

    Attributes:
        deployment_id (int): automatically generated database id. Use the id to fetch this information from the database.
        deployment_name (str, optional): optional name for a deployment
        user_id (str): a user_id associated to the deployment
        created (Date): Date of the creation of a deployment
        parameters (str): the parameters for the Job. Job parameters should already be prepared and error checked before starting the task.
        data (Union[dict, list, str, float, int, bool, None]): mutable JSON-like store for additional lightweight task data. Default value is empty dict.
    """



    deployment_id: Mapped[int] = mapped_column(primary_key=True)
    deployment_name: Mapped[Optional[str]] = mapped_column(sql.String(50), default=None)
    user_id: Mapped[str] = mapped_column(sql.String(50))
    
    __tablename__ = "Deployments"