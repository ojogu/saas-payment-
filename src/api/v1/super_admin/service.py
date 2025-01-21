#this is the service module for the super admin
#for all the crud operations available to the super admin

from api.base.service import BaseService
from api.v1.users .model import User, Role, Payment, PaymentItem, Level, Department, Session, Organization
from api.v1.users.admins.schema import create_admin
from utils.dependency import db
from typing import Optional, Any, Dict, List
from utils.exception import InUseError, NotFoundError
from .schema import organization_schema
import logging
import requests
from utils.util import get_env_value
from .model import SuperAdmin
from api.v1.auth.service import AuthService
from datetime import datetime, timedelta
from sqlalchemy import case, distinct, func, desc, and_
from typing import Optional, List, Dict

# from dataclasses import dataclass
# from decimal import Decimal
# from enum import Enum
# from api.v1.users.model import User, Payment, PaymentItem, TransactionStatus, Department, Level, RoleEnum, Session
# from utils.dependency import db
# from api.v1.auth.service import AuthService
# import logging
# from api.v1.organization.model import Organization


service_logger = logging.getLogger(__name__)
service_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/service.log')
file_handler.setFormatter(formatter)
service_logger.addHandler(file_handler)

#Crud operations for organizations
class OrganizationService(BaseService):
    def __init__(self):
        '''Sets the model to Organization and the database to db'''
        self.model = Organization
        self.db = db
    
    def get_by_email(self, email: str) -> Organization:
        """Fetches an organization by email

        Args:
            email (str): The email to search with

        Returns:
            Organization: The found organization
        """
        organization = Organization.query.filter_by(email=email).first()
        service_logger.info(f"Organization found: {organization}")
        return organization

    def create(self, data: Dict[str, Any]) -> Organization:
        """Create a new organization.

        Args:
            data (dict): The organization data

        Returns:
            Organization: The created organization

        Raises:
            EmailInUseError: If the email is already in use
            SQLAlchemyError: If there's a database error
        """
        parsed_data = organization_schema.load(data)
        service_logger.info(f"parsed data: {parsed_data}")
        
        if self.get_by_email(parsed_data['email']) is not None:
            service_logger.warning(f"Email already in use: {parsed_data['email']}")
            raise InUseError(f"Email {parsed_data['email']} is already in use")
            
        organization = Organization(**parsed_data)
        self.db.session.add(organization)
        self.db.session.commit()
        self.db.session.refresh(organization)
        service_logger.info(f"Created organization: {organization}")
        return organization
    
    def fetch_all(self, **filters: Optional[Any]) -> List[Organization]:
        '''Fetches all organization and allows for filter with query parameter by name'''

        query = self.db.session.query(Organization)

        # Enable filter by query parameter
        if filters:
            for column, value in filters.items():
                if hasattr(Organization, column) and value is not None:
                    query = query.filter(getattr(Organization, column).ilike(f'%{value}%'))

        return query.all()

    def fetch_one(self, name: Optional[str] = None, acronym: Optional[str] = None) -> Organization:
        """Fetches an organization by name or acronym

        Args:
            name (str, optional): The name to search with. Defaults to None.
            acronym (str, optional): The acronym to search with. Defaults to None.

        Returns:
            Organization: The found organization

        Raises:
            NotFoundError: If either name or acronym is not provided
        """
        if not name and not acronym:
            raise ValueError("Either name or acronym must be provided")
        query = self.db.session.query(Organization)
        if name:
            query = query.filter_by(name=name)
        if acronym:
            query = query.filter_by(acronym=acronym)
        organization = query.first()
        if organization is None:
            raise NotFoundError("Organization not found")
        return organization
    
    def update(self, acronym: str, request_data: Dict[str, Any]) -> Organization:
        
        """Updates an existing organization

        Args:
            acronym (str): The acronym of the organization to update
            request_data (dict): The data to update the organization with

        Returns:
            Organization: The updated organization

        Raises:
            NotFoundError: If the organization to update is not found
        """
        schema_data = organization_schema.load(request_data)
        organization = self.fetch_one(acronym=acronym)

        for data in schema_data.items():
            setattr(organization, *data)
        
        self.db.session.commit()
        self.db.session.refresh(organization)
        return organization
    
    def delete(self, acronym: str) -> None:
        
        """Deletes an organization by acronym

        Args:
            acronym (str): The acronym of the organization to delete

        Raises:
            NotFoundError: If the organization to delete is not found
        """
        organization = self.fetch_one(acronym=acronym)
        if organization is None:
            raise NotFoundError("Organization not found")
        self.db.session.delete(organization)
        self.db.session.commit()
        # self.db.session.refresh(organization)



class AdminManagmentService(BaseService):
    """Service class for managing admin-related operations."""
    
    def __init__(self):
        """Initializes the AdminManagmentService with the User model and database."""
        self.model = User
        self.db = db
        self.auth = AuthService(model=self.model)
    
    
    def create(self, request_data: Dict[str, Any]) -> User:
        """Creates a new admin user.
        
        Args:
            request_data (Dict[str, Any]): The data to create the admin user with.
        
        Returns:
            User: The created admin user.
        
        Raises:
            NotFoundError: If the role or organization is not found.
            EmailInUseError: If the email is already in use.
        """
        schema_data = create_admin.load(request_data)
        service_logger.info(f"Parsed admin data: {schema_data}")
        
        role_name = schema_data['role'].upper()
        organization_acronym = schema_data['organization']

        # Get the role instance and organization instance
        role_instance = self.db.session.query(Role).filter_by(name=role_name).first()
        organization_instance = self.db.session.query(Organization).filter_by(acronym=organization_acronym).first()
        
        if not role_instance or not organization_instance:
            raise NotFoundError("Role or organization not found")
        
        # Check for existing email
        existing_user = self.db.session.query(User).filter_by(email=schema_data['email']).first()
        if existing_user:
            raise InUseError("Email already exists")
        
        # Set the relationships
        schema_data['role'] = role_instance
        schema_data['organization'] = organization_instance
        
        # Set the default password and hash it
        default_password = self.auth.default_password()
        schema_data['password'] = self.auth.hash_password(default_password)
        service_logger.info(f"About to commit user: {schema_data}")
        admin = User(**schema_data)
        service_logger.info(schema_data)
        
        # Add the admin only after all checks have passed
        self.db.session.add(admin)
        self.db.session.commit()
        # self.db.session.refresh(admin)
        
        service_logger.info(f"Created admin: {admin}")
        return admin

    def bulk_create(self, data: List[Dict[str, Any]]) -> List[User]:
        """Creates multiple admin users in bulk.
        
        Args:
            data (List[Dict[str, Any]]): A list of dictionaries containing admin data.
        
        Returns:
            List[User]: A list of created admin users.
        """
        pass
    
    
    def fetch_all(self, **filters: Optional[Any]) -> List[User]:
        """Fetches all admins, allowing for filtering by query parameters.
        
        Args:
            **filters (Optional[Any]): Filters to apply to the query.
        
        Returns:
            List[User]: A list of admin users that match the filters.
        """
        criteria = {"name": "ADMIN"}
        query = self.db.session.query(User).join(Role).filter(Role.name == criteria["name"])
        
        # Enable filter by query parameter
        if filters:
            for column, value in filters.items():
                if hasattr(User, column) and value is not None:
                    query = query.filter(getattr(User, column).ilike(f'%{value}%'))

        return [{
                'id': admin.id,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                "email": admin.email,
                'role': admin.role.name,
                "phone": admin.phone,
                'organization': admin.organization.name
            } for admin in query.all()]
    
    def fetch_one(self, email: str) -> User:
        """Fetches a single admin user by email.
        
        Args:
            email (str): The email of the admin user to fetch.
        
        Returns:
            User: The fetched admin user.
        
        Raises:
            NotFoundError: If the admin user is not found.
        """
        admin = self.db.session.query(User).join(Role).filter(User.email == email, Role.name == "ADMIN").first()
        if not admin:
            raise NotFoundError("Admin user not found")
        return admin
    
    def update(self, email: str, request_data: Dict[str, Any]) -> User:
        """Updates an existing admin user.
        
        Args:
            email (str): The email of the admin user to update.
            request_data (Dict[str, Any]): The data to update the admin user with.
        
        Returns:
            User: The updated admin user.
        
        Raises:
            NotFoundError: If the admin user is not found.
        """
        admin = self.fetch_one(email=email)
        schema_data = create_admin.load(request_data)
        
        for key, value in schema_data.items():
            setattr(admin, key, value)
        
        self.db.session.commit()
        self.db.session.refresh(admin)
        service_logger.info(f"Updated admin: {admin}")
        return admin
    
    def delete(self, email: str) -> None:
        """Deletes an admin user by email.
        
        Args:
            email (str): The email of the admin user to delete.
        
        Raises:
            NotFoundError: If the admin user is not found.
        """
        admin = self.fetch_one(email=email)
        self.db.session.delete(admin)
        self.db.session.commit()
        service_logger.info(f"Deleted admin: {admin}")


class SuperAdminManagment():
    pass

class PlatformPayment():
    def __init__(self):
        self.url ="https://api.paystack.co/transaction"
        self.total_url = "https://api.paystack.co/transaction/totals"
        self.auth = AuthService(model=SuperAdmin())
        self.paystack_secret_key = get_env_value("PRIVATE_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.paystack_secret_key}",
        "Content-Type": "application/json"
        }
    def fetch_all_transcation(self):
        response = requests.post(url=self.url, headers=self.headers)
        return response.json()
    
    def fetch_total_transcation(self):
        response = requests.post(url=self.total_url, headers=self.headers)
        return response.json()


class SuperAdminAnalyticsService:
    def __init__(self):
        self.db = db
        self.auth_service = AuthService(model=SuperAdmin)

    def get_payment_analytics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Get payment analytics for the whole platform"""
        filters = {}

        # Build date filter
        date_filter = and_(
            Payment.payment_date >= start_date if start_date else True,
            Payment.payment_date <= end_date if end_date else True
        )

        # Apply analytics aggregations
        query = self.db.session.query(
            func.count(Payment.id).label('total_transactions'),
            func.sum(Payment.amount).label('total_amount'),
            func.avg(Payment.amount).label('average_payment'),
            func.count(case((Payment.status == 'Paid', 1))).label('successful_payments'),
            func.count(case((Payment.status == 'Failed', 1))).label('failed_payments'),
            func.min(Payment.amount).label('min_payment'),
            func.max(Payment.amount).label('max_payment'),
            func.count(case((Payment.status == 'Pending', 1))).label('pending_payments'),
            func.count(case((Payment.status == 'Refunded', 1))).label('refunded_payments')
        ).filter(date_filter)

        results = query.first()
        
        if not results:
            return {
                'total_transactions': 0,
                'total_amount': 0.0,
                'average_payment': 0.0,
                'successful_payments': 0,
                'failed_payments': 0,
                'success_rate': 0.0,
                'min_payment': 0.0,
                'max_payment': 0.0,
                'pending_payments': 0,
                'refunded_payments': 0
            }

        total_transactions = results[0] or 0
        total_amount = float(results[1] or 0)
        average_payment = float(results[2] or 0)
        successful_payments = results[3] or 0
        failed_payments = results[4] or 0
        min_payment = float(results[5] or 0)
        max_payment = float(results[6] or 0)
        pending_payments = results[7] or 0
        refunded_payments = results[8] or 0

        success_rate = (successful_payments / total_transactions * 100) if total_transactions > 0 else 0

        return {
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'average_payment': average_payment,
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'success_rate': round(success_rate, 2),
            'min_payment': min_payment,
            'max_payment': max_payment,
            'pending_payments': pending_payments,
            'refunded_payments': refunded_payments
        }

    def get_registration_analytics(self) -> Dict:
        """Get registration analytics for the whole platform"""
        query = self.db.session.query(User)

        total_users = query.count()
        users_by_level = query.with_entities(
            Level.name, func.count(User.id)
        ).join(Level).group_by(Level.name).all()
        
        users_by_department = query.with_entities(
            Department.name, func.count(User.id)
        ).join(Department).group_by(Department.name).all()

        return {
            'total_users': total_users,
            'users_by_level': dict(users_by_level),
            'users_by_department': dict(users_by_department)
        }

    def get_payment_trends(self, days: int = 30) -> List[Dict]:
        """Get payment trends over time for the whole platform"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = self.db.session.query(
            func.date(Payment.payment_date).label('date'),
            func.sum(Payment.amount).label('daily_total'),
            func.count(Payment.id).label('daily_count')
        ).filter(Payment.payment_date.between(start_date, end_date))

        return [
            {
                'date': row.date.strftime('%Y-%m-%d'),
                'total_amount': float(row.daily_total or 0),
                'transaction_count': row.daily_count
            }
            for row in query.group_by(func.date(Payment.payment_date))
            .order_by(func.date(Payment.payment_date)).all()
        ]

    def get_popular_payment_items(self, limit: int = 10) -> List[Dict]:
        """Get most popular payment items for the whole platform"""
        query = self.db.session.query(
            PaymentItem.name,
            func.count(Payment.id).label('payment_count'),
            func.sum(Payment.amount).label('total_amount')
        ).join(Payment)

        return [
            {
                'name': row.name,
                'payment_count': row.payment_count,
                'total_amount': float(row.total_amount or 0)
            }
            for row in query.group_by(PaymentItem.name)
            .order_by(desc('payment_count')).limit(limit).all()
        ]

    def get_department_performance(self) -> List[Dict]:
        """Get department performance metrics for the whole platform"""
        query = self.db.session.query(
            Department.name,
            func.count(distinct(User.id)).label('student_count'),
            func.count(Payment.id).label('payment_count'),
            func.sum(Payment.amount).label('total_amount'),
            func.avg(Payment.amount).label('average_payment')
        ).join(User, Department.id == User.department_id)\
         .outerjoin(Payment, User.id == Payment.user_id)

        return [
            {
                'department': row.name,
                'student_count': row.student_count,
                'payment_count': row.payment_count,
                'total_amount': float(row.total_amount or 0),
                'average_payment': float(row.average_payment or 0)
            }
            for row in query.group_by(Department.name).all()
        ]

    def get_session_analytics(self, session_id: Optional[int] = None) -> Dict:
        """Get analytics for specific academic session for the whole platform"""
        query = self.db.session.query(
            Session.name,
            func.count(distinct(User.id)).label('total_students'),
            func.count(Payment.id).label('total_payments'),
            func.sum(Payment.amount).label('total_amount')
        ).join(Level)\
         .join(User)\
         .outerjoin(Payment)

        if session_id:
            query = query.filter(Session.id == session_id)

        result = query.group_by(Session.name).first()
        
        if not result:
            return {}

        return {
            'session_name': result.name,
            'total_students': result.total_students,
            'total_payments': result.total_payments,
            'total_amount': float(result.total_amount or 0),
            'average_payment_per_student': float(result.total_amount / result.total_students if result.total_students else 0)
        }

