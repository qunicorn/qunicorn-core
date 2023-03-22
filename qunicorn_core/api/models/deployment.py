"""Module containing all API schemas for tasks in the Deployment API."""

import marshmallow as ma
from marshmallow import fields, ValidationError
from ..util import MaBaseSchema

__all__ = ["PreDeploymentSchema",]


class PreDeploymentSchema(MaBaseSchema):
    provider = ma.fields.Str(required=True, example="IBMQ")
    qpu = ma.fields.Str(required=True)
    credentials = ma.fields.Dict(
        keys=ma.fields.Str(), values=ma.fields.Str(), required=True
    )
    shots = ma.fields.Int(required=False)
    noise_model = ma.fields.Str(required=False)
    only_measurement_errors = ma.fields.Boolean(required=False)
    circuit_format = ma.fields.Str(required=False)
    parameters = ma.fields.List(ma.fields.Float(), required=False)
