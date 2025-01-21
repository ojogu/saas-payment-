from api.base.schema import BaseSchema
from marshmallow import fields

class SubAdminSchema(BaseSchema):
    """
    SubAdminSchema is a schema for validating and serializing sub-admin user data.

    Attributes:
        first_name (str): The first name of the sub-admin.
        last_name (str): The last name of the sub-admin.
        organization (str): The organization the sub-admin belongs to.
        department (str): The department the sub-admin works in.
        phone (str): The phone number of the sub-admin.
        email (str): The email address of the sub-admin.
        role (str): The role of the sub-admin within the organization.
    """
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    organization = fields.String()
    department = fields.String(required=True)
    phone = fields.String(required=True)
    email = fields.Email()
    role = fields.String(required=True)


sub_admin_schema = SubAdminSchema()
sub_admins_schema = SubAdminSchema(many=True)
sub_admin_dump_schema = SubAdminSchema(only=("first_name", "last_name", "organization", "department", "phone", "email",  "role"))


class DepartmentSchema(BaseSchema):
    name = fields.String(required=True)
    organization = fields.String()
    active_session = fields.String()
    utility = fields.Boolean()
    
department_schema = DepartmentSchema(exclude=['created_at', 'updated_at'])


class PaymentItems(BaseSchema):
    name = fields.String(required=True)
    description = fields.String(required=True)
    amount = fields.Decimal(required=True, as_string=True)
    level = fields.String(required=True)
    organization = fields.String(dump_only=True)
    department = fields.String(required=True)
    account_name = fields.String()
    academic_session = fields.String(required=True)
    status = fields.String(dump_only=True)
    subaccount_code = fields.String(dump_only=True)
    bank_name = fields.String(required=True)
    account_number = fields.String(required=True)
    percentage_charge = fields.String(required=True)
    # Example JSON for PaymentItems schema
    # example_payment_item = {
    #     "name": "Subscription Fee",
    #     "description": "Monthly subscription fee for premium services",
    #     "amount": 29.99,
    #     "level": 1,
    #     "sessions": "2023-2024"
    # }

payment_item_schema = PaymentItems(exclude=['created_at', 'updated_at'])
payment_items_schema = PaymentItems(many=True)
payment_item_dump_schema = PaymentItems(only=("id", "name", "description", "amount", "level", "organization", "department", "status"))