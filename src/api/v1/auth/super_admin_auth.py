#super admin auth

from flask import Blueprint, request
from flask_restful import Resource, Api
from .service import AuthService
from utils.response import custom_response
from .schema import super_admin__dump_schema, super_admin__login_dump_schema
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import logging
from api.v1.super_admin.model import SuperAdmin
from utils.exception import InUseError, NotFoundError, AlreadyExistsError, InvalidEmailPassword

super_admin_auth_blueprint = Blueprint("super_admin_auth", __name__, url_prefix="/api/superadmin")
super_admin_auth = Api(super_admin_auth_blueprint)

# Set up logging
auth_logger = logging.getLogger(__name__)
auth_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/auth.log')
file_handler.setFormatter(formatter)
auth_logger.addHandler(file_handler)

class Super_Admin_Register(Resource):
    """
    Super_Admin_Register is a Flask-RESTful resource for handling the registration of super admins.

    Methods:
        __init__:
            Initializes the Super_Admin_Register resource with an AuthService instance and a custom response handler.

        post:
            Handles the HTTP POST request to create a new super admin.
            - If the request does not contain JSON, returns a JSON missing error response.
            - If the request contains valid JSON, attempts to create a new super admin using the provided data.
            - On successful creation, returns a success response with the created admin's data.
            - Handles SQLAlchemyError and returns a server error response.
            - Handles ValueError (e.g., email already in use) and returns an email in use error response.
    """
    def __init__(self):
        self.service = AuthService(model=SuperAdmin)
        self.custom_response = custom_response
    def post(self):
        try:
            if not request.is_json:
                return self.custom_response.json_missing_error()
            admin =  self.service.create(request.get_json())
            return self.custom_response.success_response(
                message="Admin successfully created",
                data=super_admin__dump_schema.dump(admin),
                status_code=201
            )
        except SQLAlchemyError as e:
            auth_logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except AlreadyExistsError as e:
            auth_logger.error(f"Already exists: {str(e)}")
            return self.custom_response.not_found_error()

        
    
class Super_Admin_Login(Resource):
    """
    Resource class for handling super admin login requests.
    Methods
    -------
    __init__():
        Initializes the Super_Admin_Login resource with AuthService and custom_response.
    post():
        Handles POST requests for super admin login.
        - Validates the request JSON.
        - Authenticates the user using email and password.
        - Generates access and refresh tokens upon successful authentication.
        - Returns appropriate JSON responses for different scenarios (success, missing data, authentication failure, database error, user not found).
    Attributes
    ----------
    service : AuthService
        Service for handling authentication logic.
    custom_response : CustomResponse
        Utility for generating custom JSON responses.
    """
    def __init__(self):
        self.service = AuthService(model=SuperAdmin)
        self.custom_response = custom_response
    def post(self):
        try:
            if not request.is_json:
                return self.custom_response.json_missing_error()
            email = request.json.get("email")
            password = request.json.get("password")
            if not email or not password:
                auth_logger.error("Email and password are required")
                return self.custom_response.bad_request_error("Email and password are required")
            
            user = self.service.authenticate_user(email, password)
            auth_logger.info(user)
            if not user:
                return self.custom_response.not_found_error()
            access_token = create_access_token(identity=user.entity_id)
            refresh_token = create_refresh_token(identity=user.entity_id)
            auth_logger.info("Login successful")
            return self.custom_response.success_response(
                message="Login successful",
                data={"access_token": access_token, "refresh_token": refresh_token},
                status_code=200
            )
        except SQLAlchemyError as e:
            auth_logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            auth_logger.error(f"User not found: {str(e)}")
            return self.custom_response.not_found_error()
        except InvalidEmailPassword as e:
            auth_logger.error(f"Invalid: {str(e)}")
            return self.custom_response.unauthorized_error()
    
class Super_Admin_Refresh(Resource):
    def __init__(self):
        self.custom_response = custom_response

    @jwt_required(refresh=True)
    def post(self):
        try:
            current_user = get_jwt_identity()
            new_access_token = create_access_token(identity=current_user)
            return self.custom_response.success_response(
                message="Token refreshed",
                data=new_access_token,
                status_code=200
            )
        except Exception as e:
                auth_logger.error(f"Token refresh error: {str(e)}")
                return self.custom_response.server_error()

super_admin_auth.add_resource(Super_Admin_Refresh, "/refresh")
super_admin_auth.add_resource(Super_Admin_Register, "/register")
super_admin_auth.add_resource(Super_Admin_Login, "/login")
