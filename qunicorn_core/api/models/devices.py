"""Module containing all API schemas for tasks in the Devices API."""

import marshmallow as ma
from ..util import MaBaseSchema

__all__ = ["DevicesSchema", "DeviceIDSchema"]

class DevicesSchema(MaBaseSchema):
    service_types = ma.fields.List(cls_or_instance= ma.fields.Str() ,required=True, allow_none=False, metadata={
        "description" :  "List of available services which can be used with a device."
        })
    device_id = ma.fields.Integer(required=True, allow_none=False, metadata={
        "description" :  "The unique deviceID."
        })
    name = ma.fields.String(required=True, allow_none=False, metadata={
        "description" :  "The name of a device."
        })
    address_url = ma.fields.String(required=True, allow_none=False, metadata={
        "description" :  "URL of a device."
        })
    status = ma.fields.String(required=True, allow_none=False, metadata={
        "description" :  "Availability of a device. [Available], [Not_Available]"
        })
    description = ma.fields.String(required=True, allow_none=False, metadata={
        "description" :  "Short description of a device."
        })
    simulator = ma.fields.Boolean(required=True, allow_none=False, metadata={
        "description" :  "Whether the device is a simulator or a QPU."
        })

class DeviceIDSchema(MaBaseSchema):
    device_type = ma.fields.String(required=True, allow_none=False)
    device_id = ma.fields.Integer(required=True, allow_none=False)

class DevicesRequestSchema(MaBaseSchema):
    pass

class DevicesResponseSchema(MaBaseSchema):
    pass