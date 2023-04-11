from typing import Optional, Sequence, List, Union

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import sqltypes as sql
from sqlalchemy.sql import sqltypes as sql
from sqlalchemy.sql.expression import select
from sqlalchemy.sql.schema import ForeignKey
from .deployments import DeploymentDataclass

from ..db import MODEL, REGISTRY

@REGISTRY.mapped_as_dataclass
class TestDataclass:
    __tablename__ = "Jobs"

    job_id: Mapped[int] = mapped_column(primary_key=True)
    job_name: Mapped[Optional[str]] = mapped_column(sql.String(50), default=None)
    user_id: Mapped[str] = mapped_column(sql.String(50))
    deployment_id: Mapped[int] = mapped_column(ForeignKey("DeploymentDataclass.deployment_id"))