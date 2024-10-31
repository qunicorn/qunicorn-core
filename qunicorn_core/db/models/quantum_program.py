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

from typing import Optional

from sqlalchemy import ForeignKey, Select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import sqltypes as sql, or_

from . import deployment as deployment_model
from .db_model import DbModel, T
from ..db import REGISTRY


@REGISTRY.mapped_as_dataclass
class QuantumProgramDataclass(DbModel):
    """Dataclass for storing QuantumPrograms

    Attributes:
        id (int): The ID of the quantum program. (set by the database)
        quantum_circuit (str|None): Quantum code that needs to be executed.
        assembler_language (str|None): Assembler language in which the code should be interpreted.
        deployment (DeploymentDataclass, optional): The deployment where a list of quantum program is used.
        python_file_path (str|None): Part of experimental feature: path to file to be uploaded (to IBM).
        python_file_metadata (str|None): Part of experimental feature: metadata for the python_file.
        python_file_options (str, optional): Part of experimental feature: options for the python_file.
        python_file_input (str, optional): Part of experimental feature: inputs for the python_file.
    """

    # non-default arguments
    id: Mapped[int] = mapped_column(sql.INTEGER(), primary_key=True, autoincrement=True, init=False)
    quantum_circuit: Mapped[Optional[str]] = mapped_column(sql.Text(), nullable=True)
    assembler_language: Mapped[Optional[str]] = mapped_column(sql.String(50), nullable=True)
    # default arguments
    deployment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("Deployment.id", ondelete="CASCADE"), default=None, nullable=True, init=False
    )
    deployment: Mapped[Optional["deployment_model.DeploymentDataclass"]] = relationship(
        lambda: deployment_model.DeploymentDataclass, back_populates="programs", lazy="selectin", default=None
    )

    translations: Mapped[list["TranslatedProgramDataclass"]] = relationship(
        lambda: TranslatedProgramDataclass,
        back_populates="program",
        lazy="select",
        cascade="all, delete-orphan",
        default_factory=list,
    )

    # Experimental
    python_file_path: Mapped[Optional[str]] = mapped_column(sql.String(500), default=None, nullable=True)
    python_file_metadata: Mapped[Optional[str]] = mapped_column(sql.String(500), default=None, nullable=True)
    python_file_options: Mapped[Optional[str]] = mapped_column(sql.String(500), default=None, nullable=True)
    python_file_inputs: Mapped[Optional[str]] = mapped_column(sql.String(500), default=None, nullable=True)

    @classmethod
    def apply_authentication_filter(cls, query: Select[T], user_id: Optional[str]) -> Select[T]:
        query = query.join(deployment_model.DeploymentDataclass)
        if user_id is None:
            return query.where(deployment_model.DeploymentDataclass.deployed_by == None)  # noqa: E711
        return query.where(
            or_(
                deployment_model.DeploymentDataclass.deployed_by == None,  # noqa: E711
                deployment_model.DeploymentDataclass.deployed_by == user_id,
            )
        )


@REGISTRY.mapped_as_dataclass
class TranslatedProgramDataclass(DbModel):
    """Dataclass for storing Translated QuantumPrograms

    Attributes:
        id (int): The ID of the quantum program. (set by the database)
        quantum_circuit (bytes|None): Quantum code that needs to be executed.
        assembler_language (str|None): Assembler language in which the code should be interpreted.
        translation_distance (int): The distance of this translation from the source.
        program_id (QuantumProgramDataclass, optional): The QuanrumProgram this translation is based on.
    """

    # non-default arguments
    id: Mapped[int] = mapped_column(sql.INTEGER(), primary_key=True, autoincrement=True, init=False)
    quantum_circuit: Mapped[bytes] = mapped_column(sql.LargeBinary(), nullable=False)
    is_string: Mapped[bool] = mapped_column(sql.BOOLEAN(), nullable=False)
    assembler_language: Mapped[str] = mapped_column(sql.String(50), nullable=False)
    translation_distance: Mapped[int] = mapped_column(sql.INTEGER(), nullable=False)

    # default arguments
    program_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(QuantumProgramDataclass.id, ondelete="CASCADE"), default=None, nullable=True, init=False
    )
    program: Mapped[Optional[QuantumProgramDataclass]] = relationship(
        QuantumProgramDataclass, back_populates="translations", lazy="select", default=None
    )

    @property
    def circuit(self) -> str | bytes:
        if self.is_string:
            return self.quantum_circuit.decode()
        return self.quantum_circuit
