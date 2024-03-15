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
from typing import List

from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import select
from sqlalchemy.sql import sqltypes as sql

from . import device
from .db_model import DbModel
from .provider_assembler_language import ProviderAssemblerLanguageDataclass
from ..db import DB, REGISTRY
from ...static.qunicorn_exception import QunicornError


def _create_language_from_string(language: str):
    lang = ProviderAssemblerLanguageDataclass(language=language)
    lang.save()
    return lang


@REGISTRY.mapped_as_dataclass
class ProviderDataclass(DbModel):
    """Dataclass for storing Providers

    Attributes:
        id (int): The id of a provider. (set by the database)
        name (str): Name of the cloud service.
        with_token (bool): If authentication is needed and can be done by passing a token this attribute is true.
        supported_languages (List[str]): The programming languages that are supported by this provider. (WARNING: cannot be set in constructor!)
    """

    # non-default arguments
    id: Mapped[int] = mapped_column(sql.INTEGER(), primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(sql.String(50))
    with_token: Mapped[bool] = mapped_column(sql.BOOLEAN)
    # default arguments
    supported_languages: AssociationProxy[List[str]] = association_proxy(
        # association proxy is not part of constructor as this does not work correctly...
        "_supported_languages",
        "language",
        creator=_create_language_from_string,
        default_factory=list,
        init=False,
    )
    _supported_languages: Mapped[List[ProviderAssemblerLanguageDataclass]] = relationship(
        ProviderAssemblerLanguageDataclass,
        lazy="selectin",
        back_populates="provider",
        order_by=ProviderAssemblerLanguageDataclass.id,
        cascade="all, delete-orphan",
        default_factory=list,
        init=False,
    )
    devices: Mapped[List["device.DeviceDataclass"]] = relationship(
        lambda: device.DeviceDataclass,
        lazy="select",
        back_populates="provider",
        cascade="all, delete-orphan",
        default_factory=list,
        init=False,
    )

    @classmethod
    def get_by_name(cls, name: str):
        """Returns all providers matching the given name"""
        q = select(cls).where(cls.name == name)
        providers = DB.session.execute(q).scalars().all()

        if len(providers) < 1:
            return None
        if len(providers) > 1:
            raise QunicornError(f"Found multiple providers with the same name '{name}'!")

        return providers[0]
