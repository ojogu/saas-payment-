from utils.dependency import ma

from marshmallow import fields

class BaseSchema(ma.Schema):
    """
    BaseSchema is a Marshmallow schema that defines the basic fields and metadata
    for serializing and deserializing objects. It includes the following fields:
    Attributes:
        id (fields.Integer): An integer field that is only included in the output.
        unique_id (fields.String): A string field that is only included in the output.
        created_at (fields.DateTime): A datetime field that is only included in the output,
            formatted as "%Y-%m-%dT%H:%M:%S".
        updated_at (fields.DateTime): A datetime field that is only included in the output,
            formatted as "%Y-%m-%dT%H:%M:%S".
    Meta:
        ordered (bool): Ensures that the fields are serialized in the order they are defined.
    """
    
    id = fields.Integer(dump_only=True)
    unique_id = fields.String(dump_only=True)

    created_at = fields.DateTime(dump_only=True, format="%Y-%m-%dT%H:%M:%S")
    updated_at = fields.DateTime(dump_only=True, format="%Y-%m-%dT%H:%M:%S")

