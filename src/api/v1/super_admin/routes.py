#api routes for super admin

import datetime
from typing import Dict
from flask import Blueprint, request
from flask_restful import Resource, Api
from .service import OrganizationService, AdminManagmentService, SuperAdminAnalyticsService
from .schema import organization_schema
from api.v1.users.admins.schema import admin_dump
from utils.response import custom_response
from sqlalchemy.exc import SQLAlchemyError
from utils.exception import InUseError, NotFoundError
from flask_jwt_extended import jwt_required
from api.v1.auth.decorators import check_role_permission
import logging

super_admin_blueprint = Blueprint("super_admin", __name__, url_prefix="/api/superadmin/")
super_admin_api = Api(super_admin_blueprint)

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


class OrganizationResource(Resource):
    """
    Handles requests related to organizations.

    Attributes:
        service (OrganizationService): The service used to interact with the database.
        custom_response (custom_response): A custom response object used to generate responses.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = OrganizationService()
        self.custom_response = custom_response

    method_decorators = [check_role_permission(["SUPERADMIN"]), jwt_required()]
    def post(self) -> tuple:
        """
        Creates a new organization.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            organization = self.service.create(request.get_json())
            return self.custom_response.success_response(
                message="Organization successfully created",
                data=organization_schema.dump(organization),
                status_code=201
            )
        except InUseError as e:
            logger.warning(str(e))
            return self.custom_response.email_in_use_error()
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()


class Get_All_Organizations(Resource):
    """
    Handles requests to fetch all organizations.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = OrganizationService()
        self.custom_response = custom_response

    method_decorators = [check_role_permission(["SUPERADMIN"]), jwt_required()]
    def get(self, filters: dict = None) -> tuple:
        """
        Fetches all organizations.

        Args:
            filters (dict): A dictionary containing filters to apply to the query.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            if filters is None:
                filters = request.args.to_dict()
            organizations = self.service.fetch_all(**filters)
            return self.custom_response.success_response(
                message="All organizations fetched successfully",
                data=organization_schema.dump(organizations, many=True),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return self.custom_response.server_error()


class RetrieveUpdateDeleteOrganization(Resource):
    """
    Handles requests to retrieve, update, and delete organizations.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = OrganizationService()
        self.custom_response = custom_response

    method_decorators = [check_role_permission(["SUPERADMIN"]), jwt_required()]
    def get(self, name: str = None, acronym: str = None) -> tuple:
        """
        Retrieves a specific organization.

        Args:
            name (str): The name of the organization to retrieve.
            acronym (str): The acronym of the organization to retrieve.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            organization = self.service.fetch_one(name=name, acronym=acronym)
            return self.custom_response.success_response(
                message="Organization fetched successfully",
                data=organization_schema.dump(organization),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Value error: {str(e)}")
            return self.custom_response.not_found_error()

    def put(self, acronym: str) -> tuple:
        """
        Updates a specific organization.

        Args:
            acronym (str): The acronym of the organization to update.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            organization = self.service.update(acronym, request.get_json())
            return self.custom_response.success_response(
                message="Organization updated successfully",
                data=organization_schema.dump(organization),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return self.custom_response.server_error()

    def delete(self, acronym: str) -> tuple:
        """
        Deletes a specific organization.

        Args:
            acronym (str): The acronym of the organization to delete.

        Returns:
            A tuple containing a message and a status code.
        """
        try:
            self.service.delete(acronym)
            return self.custom_response.success_response(
                message="Organization deleted successfully",
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
            return self.custom_response.bad_request_error(message="name or acroymn must be passed")
        
#organization routes
super_admin_api.add_resource(OrganizationResource, "/organization/create")
super_admin_api.add_resource(Get_All_Organizations, "/organization/all")
super_admin_api.add_resource(RetrieveUpdateDeleteOrganization, "organization/<string:acronym>")




class AdminManagement(Resource):
    """
    Handles requests related to admins.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = AdminManagmentService()
        self.custom_response = custom_response
        
    method_decorators = [check_role_permission(["SUPERADMIN"]), jwt_required()]
    def post(self) -> tuple:
        """
        Creates a new admin.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            if not request.is_json:
                return self.custom_response.json_missing_error()
            admin = self.service.create(request.get_json())
            return self.custom_response.success_response(
                message="Admin successfully created",
                data=admin_dump.dump(admin),
                status_code=201
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except InUseError as e:
            logger.error(f"Already exists: {str(e)}")
            return self.custom_response.email_in_use_error()
        except NotFoundError as e:
            logger.error(f"Role or organization not found: {str(e)}")
            return self.custom_response.not_found_error()
        


class Get_All_Admins(Resource):
    """
    Handles requests to fetch all admins.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = AdminManagmentService()
        self.custom_response = custom_response

    method_decorators = [check_role_permission(["SUPERADMIN"]), jwt_required()]
    def get(self, filters: dict = None) -> tuple:
        """
        Fetches all admins.

        Args:
            filters (dict): A dictionary containing filters to apply to the query.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            if filters is None:
                filters = request.args.to_dict()
            admins = self.service.fetch_all(**filters)
            return self.custom_response.success_response(
                message="All admins fetched successfully",
                data=admin_dump.dump(admins, many=True),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Unexpected error: {str(e)}")
            return self.custom_response.not_found_error()


class RetrieveUpdateDeleteAdmins(Resource):
    """
    Handles requests to retrieve, update, and delete admins.
    """
    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = AdminManagmentService()
        self.custom_response = custom_response
        
    method_decorators = [check_role_permission(["SUPERADMIN"]), jwt_required()]
    def get(self, email: str) -> tuple:
        """
        Retrieves a specific admin.

        Args:
            email (str): The email of the admin to retrieve.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            admin = self.service.fetch_one(email=email)
            return self.custom_response.success_response(
                message="Admin fetched successfully",
                data=admin_dump.dump(admin),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Value error: {str(e)}")
            return self.custom_response.not_found_error()
    
    def put(self, email: str) -> tuple:
        """
        Updates a specific admin.

        Args:
            email (str): The email of the admin to update.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            admin = self.service.update(email, request.get_json())
            return self.custom_response.success_response(
                message="Admin updated successfully",
                data=admin_dump.dump(admin),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Admin not found: {str(e)}")
            return self.custom_response.not_found_error()
    def delete(self, email: str) -> tuple:
        """
        Deletes a specific admin.

        Args:
            email (str): The email of the admin to delete.

        Returns:
            A tuple containing a message and a status code.
        """
        try:
            self.service.delete(email)
            return self.custom_response.success_response(
                message="Admin deleted successfully",
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Admin not found: {str(e)}")
            return self.custom_response.not_found_error()
        
#admin endpoints
super_admin_api.add_resource(AdminManagement, "/admin/create")
super_admin_api.add_resource(Get_All_Admins, "/admin/all")
super_admin_api.add_resource(RetrieveUpdateDeleteAdmins, "/admin/<string:email>")

class AnalyticsBaseResource(Resource):
    """Base Resource class for analytics endpoints"""
    
    def __init__(self):
        self.analytics_service = SuperAdminAnalyticsService()
        self.custom_response = custom_response

    def parse_date_params(self):
        """Parse and validate date parameters from request"""
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                
            return start_date, end_date
        except ValueError as e:
            logger.error(f"Error parsing date parameters: {str(e)}")
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

class PaymentAnalyticsResource(AnalyticsBaseResource):
    @jwt_required()
    @check_role_permission(["SUPERADMIN"])
    def get(self) -> Dict:
        """Get payment analytics with optional date filtering"""
        try:
            start_date, end_date = self.parse_date_params()
            
            logger.info(f"Fetching payment analytics for dates {start_date} - {end_date}")
            analytics = self.analytics_service.get_payment_analytics(
                start_date=start_date,
                end_date=end_date
            )
            
            return self.custom_response.success_response(
                message="Payment analytics retrieved successfully",
                data=analytics
            )
        except SQLAlchemyError as e:
            logger.error(f"Error in payment analytics: {str(e)}")
            return self.custom_response.error_response(
                message=str(e),
                status_code=500
            )

class RegistrationAnalyticsResource(AnalyticsBaseResource):
    @jwt_required()
    @check_role_permission(["SUPERADMIN"])
    def get(self) -> Dict:
        """Get registration analytics"""
        try:
            logger.info("Fetching registration analytics")
            analytics = self.analytics_service.get_registration_analytics()
            return self.custom_response.success_response(
                message="Registration analytics retrieved successfully",
                data=analytics
            )
        except ValueError as e:
            logger.error(f"Error in registration analytics: {str(e)}")
            return self.custom_response.error_response(
                message=str(e),
                status_code=500
            )

class PaymentTrendsResource(AnalyticsBaseResource):
    @jwt_required()
    @check_role_permission(["SUPERADMIN"])
    def get(self) -> Dict:
        """Get payment trends"""
        try:
            days = request.args.get('days', default=30, type=int)
            logger.info(f"Fetching payment trends for {days} days")
            trends = self.analytics_service.get_payment_trends(
                days=days
            )
            
            return self.custom_response.success_response(
                message="Payment trends retrieved successfully",
                data=trends
            )
        except Exception as e:
            logger.error(f"Error in payment trends: {str(e)}")
            return self.custom_response.error_response(
                message=str(e),
                status_code=500
            )

class PopularPaymentItemsResource(AnalyticsBaseResource):
    @jwt_required()
    @check_role_permission(["SUPERADMIN"])
    def get(self) -> Dict:
        """Get popular payment items"""
        try:
            limit = request.args.get('limit', default=10, type=int)
            logger.info(f"Fetching popular payment items (limit: {limit})")
            items = self.analytics_service.get_popular_payment_items(
                limit=limit
            )
            
            return self.custom_response.success_response(
                message="Popular payment items retrieved successfully",
                data=items
            )
        except Exception as e:
            logger.error(f"Error in popular payment items: {str(e)}")
            return self.custom_response.error_response(
                message=str(e),
                status_code=500
            )

class DepartmentPerformanceResource(AnalyticsBaseResource):
    @jwt_required()
    @check_role_permission(["SUPERADMIN"])
    def get(self) -> Dict:
        """Get department performance metrics"""
        try:
            logger.info("Fetching department performance metrics")
            performance = self.analytics_service.get_department_performance()
            
            return self.custom_response.success_response(
                message="Department performance metrics retrieved successfully",
                data=performance
            )
        except Exception as e:
            logger.error(f"Error in department performance: {str(e)}")
            return self.custom_response.error_response(
                message=str(e),
                status_code=500
            )

class SessionAnalyticsResource(AnalyticsBaseResource):
    @jwt_required()
    @check_role_permission(["SUPERADMIN"])
    def get(self) -> Dict:
        """Get session analytics"""
        try:
            session_id = request.args.get('session_id', type=int)
            logger.info(f"Fetching session analytics for session {session_id}")
            analytics = self.analytics_service.get_session_analytics(
                session_id=session_id
            )
            
            return self.custom_response.success_response(
                message="Session analytics retrieved successfully",
                data=analytics
            )
        except Exception as e:
            logger.error(f"Error in session analytics: {str(e)}")
            return self.custom_response.error_response(
                message=str(e),
                status_code=500
            )

super_admin_api.add_resource(PaymentAnalyticsResource, "/analytics/payments")
super_admin_api.add_resource(RegistrationAnalyticsResource, "/analytics/registrations")
super_admin_api.add_resource(PaymentTrendsResource, "/analytics/payment-trends")
super_admin_api.add_resource(PopularPaymentItemsResource, "/analytics/popular-items")
super_admin_api.add_resource(DepartmentPerformanceResource, "/analytics/department-performance")
super_admin_api.add_resource(SessionAnalyticsResource, "/analytics/sessions")
