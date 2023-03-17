"""Module containing all API schemas for tasks in the Devices API."""

import marshmallow as ma
from ..util import MaBaseSchema

__all__ = ["DevicesSchema"]

class DevicesSchema(MaBaseSchema):
    service_type = ma.fields.String(required=True, allow_none=False)
