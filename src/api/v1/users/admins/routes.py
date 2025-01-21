# the routes for the admin services. onboards sub admin, add departments to the organization etc
from flask import Blueprint, request
from flask_restful import Resource, Api
from .service import SubAdminManagement, DepartmentManagement, SessionMangement
from .schema import session_dump
from api.v1.users.subadmin.schema import sub_admin_dump_schema, sub_admin_schema, sub_admins_schema
from api.v1.users.subadmin.schema import department_schema
from utils.response import custom_response
from sqlalchemy.exc import SQLAlchemyError
from utils.exception import InUseError, NotFoundError,AlreadyExistsError
from flask_jwt_extended import jwt_required
from api.v1.auth.decorators import check_role_permission
import logging


admin_blueprint = Blueprint("admin", __name__, url_prefix="/api/admin/")
admin_api = Api(admin_blueprint)

# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("logs/error.log")

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


class SubAdminResource(Resource):
    """
    Handles requests related to subadmins.

    Attributes:
        service (SubAdminManagment): The service used to interact with the database.
        custom_response (custom_response): A custom response object used to generate responses.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = SubAdminManagement()
        self.custom_response = custom_response

    method_decorators = [check_role_permission([ "ADMIN"]), jwt_required()]
    def post(self) -> tuple:
        """
        Creates a new subadmin.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            sub_admins = self.service.create(request.get_json())
            return self.custom_response.success_response(
                message="SubAdmin successfully created",
                data=sub_admin_dump_schema.dump(sub_admins),
                status_code=201
            )
        except InUseError as e:
            logger.warning(str(e))
            return self.custom_response.email_in_use_error(message="already exists")
        except NotFoundError as e:
            logger.warning(str(e))
            return self.custom_response.not_found_error(message="role or organization not found")
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()


class GetAllSubAdmins(Resource):
    """
    Handles requests to fetch all subadmins.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = SubAdminManagement()
        self.custom_response = custom_response

    method_decorators = [check_role_permission(["SUPERADMIN", "ADMIN"]), jwt_required()]
    def get(self, filters: dict = None) -> tuple:
        """
        Fetches all subadmins.

        Args:
            filters (dict): A dictionary containing filters to apply to the query.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            if filters is None:
                filters = request.args.to_dict()
            sub_admins = self.service.fetch_all(**filters)
            return self.custom_response.success_response(
                message="All subadmins fetched successfully",
                data=sub_admins_schema.dump(sub_admins, many=True),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()



class RetrieveUpdateDeleteSubAdmin(Resource):
    """
    Handles requests to retrieve, update, and delete subadmins.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = SubAdminManagement()
        self.custom_response = custom_response

    # method_decorators = [check_role_permission(["SUPERADMIN", "ADMIN"]), jwt_required()]
    @jwt_required()
    @check_role_permission(["SUPERADMIN", "ADMIN"])
    def get(self, email: str = None) -> tuple:
        """
        Retrieves a specific subadmin.

        Args:
            name (str): The name of the subadmin to retrieve.
            email (str): The email of the subadmin to retrieve.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            sub_admin = self.service.fetch_one( email=email)
            return self.custom_response.success_response(
                message="SubAdmin fetched successfully",
                data=sub_admin_dump_schema.dump(sub_admin),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Value error: {str(e)}")
            return self.custom_response.not_found_error()

    @jwt_required()
    @check_role_permission([ "ADMIN"])
    def put(self, email: str) -> tuple:
        """
        Updates a specific subadmin.

        Args:
            email (str): The email of the subadmin to update.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            sub_admin = self.service.update(email, request.get_json())
            return self.custom_response.success_response(
                message="SubAdmin updated successfully",
                data=sub_admin_dump_schema.dump(sub_admin),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return self.custom_response.server_error()
        
        
    @jwt_required()
    @check_role_permission([ "ADMIN"])
    def delete(self, email: str) -> tuple:
        """
        Deletes a specific subadmin.

        Args:
            email (str): The email of the subadmin to delete.

        Returns:
            A tuple containing a message and a status code.
        """
        try:
            self.service.delete(email)
            return self.custom_response.success_response(
                message="SubAdmin deleted successfully",
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found: {str(e)}")
            return self.custom_response.not_found_error(message=f"{email} not found")
        except ValueError as e:
            logger.error(f" {str(e)}")
            return self.custom_response.bad_request_error(message="email must be passed")
        
# subadmin routes
admin_api.add_resource(SubAdminResource, "/subadmin/create")
admin_api.add_resource(GetAllSubAdmins, "/subadmin/all")
admin_api.add_resource(RetrieveUpdateDeleteSubAdmin, "subadmin/<string:email>")


class GeneralOrganizationResource(Resource):
    pass 

class DepartmentResource(Resource):
    """
    Handles requests related to departments.

    Attributes:
        service (DepartmentService): The service used to interact with the database.
        custom_response (custom_response): A custom response object used to generate responses.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = DepartmentManagement()
        self.custom_response = custom_response
        

    method_decorators = [check_role_permission(["ADMIN"]), jwt_required()]
    def post(self) -> tuple:
        """
        Creates a new department.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            department = self.service.create(request.get_json())
            return self.custom_response.success_response(
                message="Department successfully created",
                data=department_schema.dump(department),
                status_code=201
            )
        except InUseError as e:
            logger.warning(str(e))
            return self.custom_response.email_in_use_error()
        except AlreadyExistsError as e:
            logger.warning(str(e))
            return self.custom_response.bad_request_error(message="already exists")
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()


class GetAllDepartments(Resource):
    """
    Handles requests to fetch all departments.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = DepartmentManagement()
        self.custom_response = custom_response

    method_decorators = [check_role_permission(["SUPERADMIN", "ADMIN"]), jwt_required()]
    def get(self, filters: dict = None) -> tuple:
        """
        Fetches all departments.

        Args:
            filters (dict): A dictionary containing filters to apply to the query.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            if filters is None:
                filters = request.args.to_dict()
            departments = self.service.fetch_all(**filters)
            return self.custom_response.success_response(
                message="All departments fetched successfully",
                data=department_schema.dump(departments, many=True),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return self.custom_response.server_error()


class RetrieveUpdateDeleteDepartment(Resource):
    """
    Handles requests to retrieve, update, and delete departments.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = DepartmentManagement()
        self.custom_response = custom_response

    # method_decorators = [check_role_permission(["SUPERADMIN", "ADMIN"]), jwt_required()]
    @jwt_required()
    @check_role_permission(["SUPERADMIN", "ADMIN"])
    def get(self, name: str = None, code: str = None) -> tuple:
        """
        Retrieves a specific department.

        Args:
            name (str): The name of the department to retrieve.
            code (str): The code of the department to retrieve.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            department = self.service.fetch_one(name=name, code=code)
            return self.custom_response.success_response(
                message="Department fetched successfully",
                data=department_schema.dump(department),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Value error: {str(e)}")
            return self.custom_response.not_found_error()

    @jwt_required()
    @check_role_permission([ "ADMIN"])
    def put(self, name: str) -> tuple:
        """
        Updates a specific department.

        Args:
            code (str): The code of the department to update.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            department = self.service.update(name, request.get_json())
            return self.custom_response.success_response(
                message="Department updated successfully",
                data=department_schema.dump(department),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        
    @jwt_required()
    @check_role_permission([ "ADMIN"])
    def delete(self, name: str) -> tuple:
        """
        Deletes a specific department.

        Args:
            code (str): The code of the department to delete.

        Returns:
            A tuple containing a message and a status code.
        """
        try:
            self.service.delete(name)
            return self.custom_response.success_response(
                message="Department deleted successfully",
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found: {str(e)}")
            return self.custom_response.not_found_error()
        except ValueError as e:
            logger.error(f" {str(e)}")
            return self.custom_response.bad_request_error(message="name or code must be passed")

# department routes
admin_api.add_resource(DepartmentResource, "/department/create")
admin_api.add_resource(GetAllDepartments, "/department/all")
admin_api.add_resource(RetrieveUpdateDeleteDepartment, "department/<string:name>")


class SessionResource(Resource):
    def __init__(self):
        self.service = SessionMangement()
        self.custom_response = custom_response
    
    @jwt_required()
    @check_role_permission([ "SUBADMIN", "ADMIN"])
    def post(self) -> tuple:
        try:
            session = self.service.create(request.get_json())
            return self.custom_response.success_response(
                message="Session successfully created",
                data=session_dump.dump(session),
                status_code=201
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()

class Fetch_Active_Session(Resource):
    def __init__(self):
        self.service = SessionMangement()
        self.custom_response = custom_response
    
    @jwt_required()
    @check_role_permission([ "SUBADMIN", "ADMIN"])
    def get(self) -> tuple:
        try:
            session = self.service.fetch_all_active_session()
            logger.info(session)
            return self.custom_response.success_response(
                message="Session fetched successfully",
                data=session_dump.dump(session, many=True),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()

class Fetch_all_Session(Resource):
    def __init__(self):
        self.service = SessionMangement()
        self.custom_response = custom_response
    
    @jwt_required()
    @check_role_permission([ "SUBADMIN", "ADMIN"])
    def get(self) -> tuple:
        try:
            session = self.service.fetch_all()
            return self.custom_response.success_response(
                message="Session fetched successfully",
                data=session_dump.dump(session, many=True),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()


#session routes
admin_api.add_resource(SessionResource, "/session/create")
admin_api.add_resource(Fetch_all_Session, "/session/all")
admin_api.add_resource(Fetch_Active_Session, "/session/active")