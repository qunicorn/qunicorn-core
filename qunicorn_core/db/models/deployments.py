from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import sqltypes as sql

from ..db import MODEL, REGISTRY

@REGISTRY.mapped_as_dataclass
class TestDataclass:
    __tablename__ = "Deployments"

    deployment_id: Mapped[int] = mapped_column(primary_key=True)
    deployment_name: Mapped[Optional[str]] = mapped_column(sql.String(50), default=None)
    user_id: Mapped[str] = mapped_column(sql.String(50))
    