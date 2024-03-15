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

from http import HTTPStatus
from typing import Any, Optional, TypeVar

from sqlalchemy.orm import declared_attr
from sqlalchemy.sql import Select, select

from ..db import DB
from ...static.qunicorn_exception import QunicornError

T = TypeVar("T", bound=Any)


class DbModel:
    """Dataclass for database model to create a table name and the id column"""

    @declared_attr
    def __tablename__(self):
        return self.__name__.replace("Dataclass", "")

    @classmethod
    def apply_authentication_filter(cls, query: Select[T], user_id: Optional[str]) -> Select[T]:
        return query

    @classmethod
    def get_all(cls):
        """Get all database objects of this class."""
        q = select(cls)
        return DB.session.execute(q).scalars().all()

    @classmethod
    def get_all_authenticated(cls, user_id: Optional[str]):
        """Get all database objects of this class that the given user is allowed to access.

        Uses the `apply_authentication_filter` method to filter out objects.
        """
        q = cls.apply_authentication_filter(select(cls), user_id)
        return DB.session.execute(q).scalars().all()

    @classmethod
    def not_found_message(cls, id_: int) -> str:
        return f"{cls.__tablename__} with id '{id_}' was not found."

    @classmethod
    def get_by_id_query(cls, id_: int):
        """Get a select query for a single database object by its `id` attribute."""
        id_attr = getattr(cls, "id", None)
        if id_attr is None:
            raise NotImplementedError(f"Class {cls.__name__} has no 'id' attribute and cannot be queried by id!")
        return select(cls).where(id_attr == id_)

    @classmethod
    def get_by_id(cls, id_: int):
        """Get a single database object by its `id` attribute."""
        q = cls.get_by_id_query(id_)
        return DB.session.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_id_or_404(cls, id_: int):
        """Get a single database object by its `id` attribute and raise 404 error if not found."""
        q = cls.get_by_id_query(id_)
        db_object = DB.session.execute(q).scalar_one_or_none()
        if db_object is None:
            raise QunicornError(cls.not_found_message(id_), HTTPStatus.NOT_FOUND)
        return db_object

    @classmethod
    def get_by_id_authenticated(cls, id_: int, user_id: Optional[str]):
        """Get a single database object by its `id` attribute and
        return None if not found or the user has insufficient rights."""
        q = cls.get_by_id_query(id_)
        q = cls.apply_authentication_filter(q, user_id)
        return DB.session.execute(q).scalar_one_or_none()

    @classmethod
    def get_by_id_authenticated_or_404(cls, id_: int, user_id: Optional[str]):
        """Get a single database object by its `id` attribute and raise 404 error
        if not found or the user has insufficient rights."""
        q = cls.get_by_id_query(id_)
        q = cls.apply_authentication_filter(q, user_id)
        db_object = DB.session.execute(q).scalar_one_or_none()
        if db_object is None:
            raise QunicornError(cls.not_found_message(id_), HTTPStatus.NOT_FOUND)
        return db_object

    @classmethod
    def delete_by_id(cls, id_: int, commit: bool = False):
        """Delete a single database object by its `id` attribute and optionally commit all pending changes."""
        # always go through the ORM for deletes to be sure that all ORM objects
        # get properly updated!
        db_object = cls.get_by_id(id_=id_)
        if db_object:
            db_object.delete()
        if commit:  # always commit if requested
            DB.session.commit()

    def save(self, commit: bool = False):
        """Add the current object to the database and optionally commit all pending changes.

        This does not automatically create the database ids (except when commit is True).
        """
        DB.session.add(self)
        if commit:
            DB.session.commit()

    def delete(self, commit: bool = False):
        """Delete the current object and optionally commit all pending changes."""
        DB.session.delete(self)
        if commit:
            DB.session.commit()
