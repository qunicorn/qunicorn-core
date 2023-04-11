"""Module containing all API schemas for tasks in the Users API."""

import marshmallow as ma
from ..util import MaBaseSchema

__all__ = ["UsersSchema", "UserIDSchema"]

class UsersSchema(MaBaseSchema):
    user_ID = ma.fields.String(required=True, allow_none=False)
    name = ma.fields.String(required=True, allow_none=False)
    group = ma.fields.String(required=True, allow_none=False)
    privileges = ma.fields.String(required=True, allow_none=False)
    status = ma.fields.String(required=True, allow_none=False)
    description = ma.fields.String(required=False, allow_none=True)

class UserIDSchema(MaBaseSchema):
    user_id = ma.fields.String(required=True, allow_none=False)