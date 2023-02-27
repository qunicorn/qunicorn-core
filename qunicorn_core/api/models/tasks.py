"""Module containing all API schemas for tasks in the Taskmanager API."""

import marshmallow as ma
from ..util import MaBaseSchema

__all__ = [
    "TaskIDSchema",
]


class TaskIDSchema(MaBaseSchema):
    uid = ma.fields.Url(required=True, allow_none=False, dump_only=True)
    description = ma.fields.String(required=True, allow_none=False, dump_only=True)