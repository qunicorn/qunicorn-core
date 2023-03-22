"""Module containing all API schemas for tasks in the Services API."""

import marshmallow as ma
from ..util import MaBaseSchema

__all__ = ["ServicesSchema",]

class ServicesSchema(MaBaseSchema):
    service_type = ma.fields.String(required=True, allow_none=False)
    name = ma.fields.String(required=True, allow_none=False)
    address = ma.fields.String(required=True, allow_none=False)
    status = ma.fields.String(required=True, allow_none=False)
    description = ma.fields.String(required=True, allow_none=False)
    simulator = ma.fields.Boolean(required=True, allow_none=False)
    url = ma.fields.String(required=True, allow_none=False)
