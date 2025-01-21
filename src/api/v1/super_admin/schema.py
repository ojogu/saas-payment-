#this is the schema for the super admin 
from api.base.schema import BaseSchema
from marshmallow import fields 
class Organization_Schema(BaseSchema):
    """
    Schema for representing an organization.

    Attributes:
        name (str): The name of the organization.
        email (str): The email address of the organization.
        acronym (str): The acronym of the organization.
        phone (str): The phone number of the organization.
        address (str): The address of the organization.
    """
    name = fields.String(required=True)
    email = fields.Email(required=True)
    acronym = fields.String(required=True)
    phone = fields.String(required=True)
    address = fields.String(required=True)
    
organization_schema = Organization_Schema(exclude=['created_at', 'updated_at'])

