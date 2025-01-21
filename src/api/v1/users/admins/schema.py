#schema for admin creation 

from marshmallow import fields
from api.base.schema import BaseSchema

class AdminSchema(BaseSchema):
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    organization = fields.String(required=True)
    phone = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True)
    role = fields.String(required=True)
create_admin = AdminSchema()
admin_dump = AdminSchema(exclude=['password', 'created_at', 'updated_at'])

class SessionSchema(BaseSchema):
    name = fields.String(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    is_active = fields.String(required=True)
    organization = fields.String(dump_only=True)
session_schema = SessionSchema()
session_dump = SessionSchema(exclude=['created_at', 'updated_at'])


class ClearanceItemSchema(BaseSchema):
    name = fields.String(required=True)
    description  = fields.String(required=True)
    academic_session = fields.String(required=True)
    department = fields.String(required=True)
    level = fields.String(required=True)
clearance_item_schema = ClearanceItemSchema()
clearance_item_schema = ClearanceItemSchema(exclude=['created_at', 'updated_at'])