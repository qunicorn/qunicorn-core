"""Module containing all API schemas for tasks in the Services API."""

import marshmallow as ma
from ..util import MaBaseSchema

__all__ = ["ServicesSchema", "ServiceIDSchema"]

class ServicesSchema(MaBaseSchema):
    service_id = ma.fields.String(required=True, allow_none=False)
    service_type = ma.fields.String(required=True, allow_none=False)
    provider_name = ma.fields.String(required=True, allow_none=False)
    status = ma.fields.String(required=True, allow_none=False)
    description = ma.fields.String(required=True, allow_none=False)
    url = ma.fields.String(required=True, allow_none=False)

class ServiceIDSchema(MaBaseSchema):
    service_id = ma.fields.String(required=True, allow_none=False)