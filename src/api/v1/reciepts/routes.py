from .service import analytics_service
from flask_restful import Resource, Api
from flask import Blueprint, request
import datetime
from api.v1.auth.decorators import check_role_permission
from flask_jwt_extended import jwt_required
from api.v1.auth.service import AuthService
from api.v1.users.model import User, RoleEnum
from utils.response import custom_response
import logging
from sqlalchemy.exc import SQLAlchemyError  
from typing import Dict

analytics_blueprint = Blueprint("analytics", __name__, url_prefix="/api/analytics")
analytics_api = Api(analytics_blueprint)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("logs/analytics.log")

console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.ERROR)

console_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)
file_handler.setFormatter(file_format)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


class AnalyticsBaseResource(Resource):
    """Base Resource class for analytics endpoints"""
    
    def __init__(self):
        self.analytics_service = analytics_service
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
    @check_role_permission(["SUPERADMIN", "ADMIN", "BURSAR", "SUBADMIN", "STUDENT"])
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
    @check_role_permission(["SUPERADMIN", "ADMIN", "BURSAR", "SUBADMIN", "STUDENT"])
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
    @check_role_permission(["SUPERADMIN", "ADMIN", "BURSAR", "SUBADMIN", "STUDENT"])
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
    @check_role_permission(["SUPERADMIN", "ADMIN", "BURSAR", "SUBADMIN", "STUDENT"])
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
    @check_role_permission(["SUPERADMIN", "ADMIN", "BURSAR", "SUBADMIN", "STUDENT"])
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
    @check_role_permission(["SUPERADMIN", "ADMIN", "BURSAR", "SUBADMIN", "STUDENT"])
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

class AnalyticsDashboardResource(AnalyticsBaseResource):
    @jwt_required()
    @check_role_permission(["SUPERADMIN", "ADMIN", "BURSAR", "SUBADMIN", "STUDENT"])
    def get(self) -> Dict:
        """Get comprehensive dashboard analytics"""
        try:
            # Get various analytics based on user role
            dashboard_data = {}
            
            # Basic analytics available to all roles
            logger.info("Fetching payment analytics")
            dashboard_data['payment_analytics'] = self.analytics_service.get_payment_analytics()
            
            logger.info("Fetching payment trends")
            dashboard_data['payment_trends'] = self.analytics_service.get_payment_trends(days=30)
            
            logger.info("Fetching registration analytics")
            dashboard_data['registration_analytics'] = self.analytics_service.get_registration_analytics()
                
            logger.info("Fetching popular payment items")
            dashboard_data['popular_items'] = self.analytics_service.get_popular_payment_items(limit=5)
            
            # Analytics only for top-level administrators
            logger.info("Fetching department performance metrics")
            dashboard_data['department_performance'] = self.analytics_service.get_department_performance()
            
            logger.info("Fetching session analytics")
            dashboard_data['session_analytics'] = self.analytics_service.get_session_analytics(
                )
            
            return self.custom_response.success_response(
                message="Dashboard analytics retrieved successfully",
                data=dashboard_data
            )
        except ValueError as e:
            logger.error(f"Error in dashboard analytics: {str(e)}")
            return self.custom_response.error_response(
                message=str(e),
                status_code=500
            )

analytics_api.add_resource(PaymentAnalyticsResource, '/payments')
analytics_api.add_resource(RegistrationAnalyticsResource, '/registrations')
analytics_api.add_resource(PaymentTrendsResource, '/payment-trends')
analytics_api.add_resource(PopularPaymentItemsResource, '/popular-items')
analytics_api.add_resource(DepartmentPerformanceResource, '/department-performance')
analytics_api.add_resource(SessionAnalyticsResource, '/sessions')
analytics_api.add_resource(AnalyticsDashboardResource, '/dashboard')

