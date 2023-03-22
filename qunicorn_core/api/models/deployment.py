"""Module containing all API schemas for tasks in the Deployment API."""

import marshmallow as ma
from marshmallow import fields, ValidationError
from ..util import MaBaseSchema

__all__ = ["PreDeploymentSchema",]


class PreDeploymentSchema(MaBaseSchema):
    name = ma.fields.Str(required=True)
    description = ma.fields.Str(required=True)
    #credentials = ma.fields.Dict(
    #   keys=ma.fields.Str(), values=ma.fields.Str(), required=True
    #)
    #shots = ma.fields.Int(required=False)
    # Circuit, Program, Container
    deploymentType = ma.fields.Str(required=True)
    resourceURI = ma.fields.Str(required=True)
    
