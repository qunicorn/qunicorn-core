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

from typing import Optional, Union

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import select
from sqlalchemy.sql import sqltypes as sql
from sqlalchemy.sql.schema import ForeignKey

from .db_model import DbModel
from .provider import ProviderDataclass
from ..db import DB, REGISTRY
from ...static.qunicorn_exception import QunicornError


@REGISTRY.mapped_as_dataclass
class DeviceDataclass(DbModel):
    """Dataclass for storing CloudDevices of a provider

    Attributes:
        id (int): The id of the device. (set by the database)
        name (str): The name of the device.
        num_qubits (int): The amount of qubits that is available at this device.
        is_simulator (bool): The information whether the device is a simulator (true) or not (false).
        is_local (bool): The information whether jobs executed on this device are executed local or not.
        provider (ProviderDataclass): The provider of this device.
    """

    # non-default arguments
    id: Mapped[int] = mapped_column(sql.INTEGER(), primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(sql.String)
    num_qubits: Mapped[int] = mapped_column(sql.INTEGER)
    is_simulator: Mapped[bool] = mapped_column(sql.BOOLEAN)
    is_local: Mapped[bool] = mapped_column(sql.BOOLEAN)
    provider: Mapped[ProviderDataclass] = relationship(ProviderDataclass, back_populates="devices", lazy="selectin")
    # default arguments
    provider_id: Mapped[int] = mapped_column(
        ForeignKey(ProviderDataclass.id, ondelete="SET NULL"), nullable=True, default=None, init=False
    )

    @classmethod
    def get_by_name(cls, name: str, provider: Optional[Union[int, str, ProviderDataclass]] = None):
        q = select(cls).where(cls.name == name)
        if isinstance(provider, int):
            q = q.where(cls.provider_id == provider)
        elif isinstance(provider, ProviderDataclass):
            q = q.where(cls.provider == provider)
        elif isinstance(provider, str):
            # TODO test this...
            q = q.where(
                cls.provider_id == select(ProviderDataclass.id).where(ProviderDataclass.name == provider).limit(1)
            )

        devices = DB.session.execute(q).scalars().all()

        if len(devices) < 1:
            return None  # no device found
        if len(devices) > 1:
            raise QunicornError(f"Found multiple devices with the same name '{name}'!")

        return devices[0]
