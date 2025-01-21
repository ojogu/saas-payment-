#user auth

from flask import Blueprint, request
from flask_restful import Resource, Api
from utils.response import custom_response
from .schema import user_login_dump_schema, user_login_schema, password_reset_schema
from .service import AuthService
from api.v1.users.model import User
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from utils.dependency import db
from utils.exception import InUseError, NotFoundError, AlreadyExistsError, InvalidEmailPassword
import logging 


user_auth_blueprint = Blueprint("user_auth", __name__, url_prefix="/api/users")
user_auth = Api(user_auth_blueprint)

# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("logs/auth.log")

# Set level for handlers
console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.ERROR)

# Create formatters and add them to handlers
console_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)
file_handler.setFormatter(file_format)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)



class User_Login(Resource):
    def __init__(self):
        
        self.model = User
        self.db = db
        self.auth = AuthService(model=self.model)
        self.custom_response = custom_response

    def post(self):
        try:
            login_data = user_login_schema.load(request.get_json())
            # logger.info(f"login data: {login_data}")
            user = self.auth.authenticate_user(login_data["email"], login_data["password"])
            if not user:
                return self.custom_response.not_found_error()
            logger.info(f"user: {user.role.name}")
            access_token = create_access_token(identity=user.entity_id)
            if user.department is None:
                return self.custom_response.success_response(
                    message="access token created",
                    data={
                        "id": user.id,
                        "organization": user.organization.name,
                        "department": None,
                        "access-token": access_token,
                        # "role": user.role.name
                    },
                    status_code=200,
                )
            if user.level is None:
                return self.custom_response.success_response(
                    message="access token created",
                    data={
                        "id": user.id,
                        "organization": user.organization.name,
                        "department": user.department.name,
                        "level": None,
                        "access-token": access_token,
                        # "role": user.role.name
                    },
                    status_code=200,
                )
            return self.custom_response.success_response(
                message="access token created",
                data={
                    "id": user.id,
                    "organization": user.organization.name,
                    "department": user.department.name,
                    # "role": user.role.name,
                    "level": user.level.name,
                    "access-token": access_token,
                },
                status_code=200,
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"User not found: {str(e)}")
            return self.custom_response.not_found_error()
        except InvalidEmailPassword as e:
            logger.error(f"Invalid: {str(e)}")
            return self.custom_response.unauthorized_error()


class ResetPassword(Resource):
    def __init__(self):
        self.auth = AuthService(model=User)
        self.custom_response = custom_response
    
    def post(self):
        try:
            self.auth.change_password(request.get_json())
            return self.custom_response.success_response(
                message="Password reset successfully",
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"User not found: {str(e)}")
            return self.custom_response.not_found_error()

user_auth.add_resource(User_Login, "/login")
user_auth.add_resource(ResetPassword, "/reset-password")