#schema for super admin registration and the login schema which is used for login by all users

from api.base.schema import BaseSchema
from marshmallow import fields

class SuperAdminSchema_Register(BaseSchema):
    """
    Schema for registering a Super Admin.

    Attributes:
        username (str): The username of the Super Admin. This field is required.
        email (str): The email address of the Super Admin. This field is required.
        password (str): The password for the Super Admin account. This field is required.
        role (str): The role of the Super Admin. This field is required.
    """
    username = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True)
    role = fields.String(required=True)

super_admin_schema = SuperAdminSchema_Register(exclude=['created_at', 'updated_at' ])

super_admin__dump_schema = SuperAdminSchema_Register(exclude=['created_at', 'updated_at', 'password'])

class LoginSchema(BaseSchema):
    """
    LoginSchema is used to validate the login request payload.

    Attributes:
        email (str): The email address of the user. This field is required.
        password (str): The password of the user. This field is required.
    """
    email = fields.String(required=True)
    password = fields.String(required=True)
    
super_admin_login_schema = LoginSchema(exclude=['created_at', 'updated_at' ])
super_admin__login_dump_schema = LoginSchema(exclude=['created_at', 'updated_at', 'password'])

class UserLoginSchema(BaseSchema):
    """
    UserLoginSchema is a schema for validating user login data.

    Attributes:
        email (str): The email address of the user. This field is required.
        password (str): The password of the user. This field is required.
        role (str): The role of the user. This field is required.
    """
    email = fields.String(required=True)
    password = fields.String(required=True)
    role = fields.String(required=True)
    
user_login_schema = UserLoginSchema(exclude=['created_at', 'updated_at' ])
user_login_dump_schema = UserLoginSchema(exclude=['created_at', 'updated_at', 'password'])

class PasswordResetSchema(BaseSchema):
    """
    Schema for password reset
    """

    email = fields.Email(required=True)
    old_password = fields.String(required=True)
    new_password = fields.String(required=True)
    confirm_password = fields.String(required=True)
    
password_reset_schema = PasswordResetSchema(exclude=['created_at', 'updated_at' ])