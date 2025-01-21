#service class for admin
#the admin handles the management of sub-admins and users, also has accesss to the platform for its organization. it is able to create, update and delete users for its organization. view all payment made in the organization 

from sqlalchemy import func
from api.base.service import BaseService
import logging
from .schema import session_schema
from utils.dependency import db
from api.v1.users .model import User, Role, Session, PaymentItem, Payment, TransactionStatus, Organization
from api.v1.auth.service import AuthService
from utils.exception import InUseError, NotFoundError, AlreadyExistsError
from api.v1.users.subadmin.schema import sub_admin_schema, sub_admins_schema
from api.v1.users.model import Department
from api.v1.users.subadmin.schema import department_schema
from typing import Any, Optional, List, Dict
from api.v1.users .model import User
from api.v1.auth.service import AuthService
from datetime import datetime

#setup logging
service_logger = logging.getLogger(__name__)
service_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/service.log')
file_handler.setFormatter(formatter)
service_logger.addHandler(file_handler)

class SubAdminManagement(BaseService):
    def __init__(self):
        self.model = User
        self.db = db
        self.auth = AuthService(model=self.model)

    def create(self, request_data: Dict[str, Any]) -> User:
        service_logger.info("Starting subadmin creation process")
        schema_data = sub_admin_schema.load(request_data)
        clean_mail = self.auth.clean_email(schema_data["email"])
        role_name = schema_data['role'].upper()

        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Creating subadmin for organization: {organization_acronym}")

        department_name = schema_data.get("department")
        if department_name:
            department_instance = self.db.session.query(Department).join(Organization).filter(
            Organization.acronym == organization_acronym,
            Department.name == department_name
            ).first()
            if not department_instance:
                raise NotFoundError("Department not found")
            schema_data["department"] = department_instance
        
        role_instance = self.db.session.query(Role).filter_by(name=role_name).first()
        service_logger.info(f"Role query result: {role_instance}")
        organization_instance = self.db.session.query(Organization).filter_by(acronym=organization_acronym).first()
        service_logger.info(f"Organization query result: {organization_instance}")
        if not role_instance or not organization_instance:
            raise NotFoundError("Role or organization not found")

        existing_admin = self.db.session.query(self.model).filter_by(email=clean_mail).first()
        if existing_admin:
            raise InUseError("Subadmin already exists")

        schema_data["role"] = role_instance
        schema_data["organization"] = organization_instance

        default_password = self.auth.default_password()
        schema_data['password'] = self.auth.hash_password(default_password)
        service_logger.info(f"About to commit user: {schema_data}")
        # sub_admin = User(
        #     first_name=schema_data['first_name'],
        #     last_name=schema_data['last_name'],
        #     email=schema_data['email'],
        #     password=schema_data['password'],
        #     department = schema_data['department'],
        #     role=schema_data['role'],
        #     organization=schema_data['organization'],
        #     phone=schema_data['phone'],
        # )
        
        sub_admin = User(**schema_data)
        service_logger.info(f"About to commit user: {sub_admin}")
        
        self.db.session.add(sub_admin)
        self.db.session.commit()
        service_logger.info(f"Created user: {sub_admin}")
        return sub_admin

    def fetch_all(self, **filters: Optional[Any]) -> List[Dict]:
        service_logger.info("Starting fetch all subadmins process")
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Fetching all subadmins for organization: {organization_acronym}")

        query = self.db.session.query(self.model).join(Role).join(Organization).filter(
            Role.name == "SUBADMIN",
            Organization.acronym == organization_acronym
        )

        if filters:
            for column, value in filters.items():
                if hasattr(self.model, column) and value is not None:
                    query = query.filter(getattr(self.model, column).ilike(f'%{value}%'))

        result = [{
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            "role": user.role.name,
            "department": user.department.name,
            'organization': user.organization.name
        } for user in query.all()]
        service_logger.info(f"Fetched subadmins: {result}")
        return result

    def fetch_one(self, email: str) -> User:
        service_logger.info(f"Starting fetch subadmin process for email: {email}")
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Fetching subadmin for organization: {organization_acronym}")
        
        # First fetch the role
        role_instance = self.db.session.query(Role).filter_by(name="SUBADMIN").first()
        
        # Then use the role ID directly in the query instead of the role object
        user = self.db.session.query(self.model)\
            .join(Organization)\
            .filter(
                self.model.email == email,
                self.model.role_id == role_instance.id,  # Assuming your User model has role_id column
                Organization.acronym == organization_acronym
            ).first()
        
        service_logger.info(f"Fetched subadmin: {user}")
        return user

    def update(self, email: str, request_data: Dict[str, Any]) -> User:
        service_logger.info(f"Starting update subadmin process for email: {email}")
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Updating subadmin for organization: {organization_acronym}")

        user = self.fetch_one(email)

        if not user:
            raise NotFoundError("Subadmin not found")

        schema_data = sub_admin_schema.load(request_data, partial=True)

        if "email" in schema_data:
            clean_mail = self.auth.clean_email(schema_data["email"])
            existing_user = self.db.session.query(self.model).filter_by(email=clean_mail).first()
            if existing_user and existing_user.id != user.id:
                raise InUseError("Email is already in use by another user")
            user.email = clean_mail

        if "password" in schema_data:
            user.password = self.auth.hash_password(schema_data["password"])

        for key, value in schema_data.items():
            if key not in ["email", "password"]:
                setattr(user, key, value)

        self.db.session.commit()
        self.db.session.refresh(user)
        service_logger.info(f"Updated user: {user}")
        return user

    def delete(self, email: str) -> None:
        service_logger.info(f"Starting delete subadmin process for email: {email}")
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Deleting subadmin for organization: {organization_acronym}")

        user = self.fetch_one(email)
        if not user:
            raise NotFoundError("Subadmin not found")

        self.db.session.delete(user)
        self.db.session.commit()
        # service_logger.info(f"Deleted subadmin: {user}")

class GeneralOrganizationService():
    """sumary_line
    this is the general service for the organization. it manages the whole organization, from getting all organization users to payment made etc
    Keyword arguments:
    argument -- description
    Return: return_description
    """
    pass 

class DepartmentManagement(BaseService):
    def __init__(self):
        self.model = Department
        self.db = db
        self.auth = AuthService(model=User)

    def get_by_name(self, name: str, organization_acronym: str) -> Optional[Department]:
        """Fetches a department by name for a specific organization

        Args:
            name (str): The name of the department to fetch
            organization_acronym (str): The acronym of the organization to fetch from

        Returns:
            Optional[Department]: The fetched department or None if not found
        """
        service_logger.info(f"Fetching department by name: {name} for organization: {organization_acronym}")
        department = self.db.session.query(Department).join(Organization).filter(
            Organization.acronym == organization_acronym,
            Department.name == name
        ).first()
        if not department:
            service_logger.info(f"Department not found")
            return None
        else:
            service_logger.info("Department found")
            return department

    def create(self, data: Dict[str, Any]):
        service_logger.info("Starting department creation process")
        parsed_data = department_schema.load(data)
        service_logger.info(f"Parsed data: {parsed_data}")
        admin = self.auth.get_current_user()
        service_logger.info(admin.role.name)
        organization_acronym = admin.organization.acronym
        service_logger.info(organization_acronym)
        
        # Fetch the active session for the organization
        active_session = self.db.session.query(Session).join(Organization).filter(
            Organization.acronym == organization_acronym,
            Session.is_active == True
        ).first()

        if not active_session:
            raise NotFoundError("No active session found for the organization")

        # Link the active session to the department
        parsed_data["session"] = active_session

        existing_dept = self.get_by_name(parsed_data["name"], organization_acronym)
        if existing_dept:
            service_logger.warning(f"Department already exists: {parsed_data['name']}")
            raise AlreadyExistsError("Department already exists")
        
        organization_instance = self.db.session.query(Organization).filter_by(acronym=organization_acronym).first()
        if not organization_instance:
            raise NotFoundError("Organization not found")

        #linking the department to the organization
        parsed_data["organization"] = organization_instance

        department = Department(**parsed_data)
        self.db.session.add(department)
        self.db.session.commit()
        service_logger.info(f"Created department: {department}")
        return department
    
    def fetch_all(self, **filters: Optional[Any]) -> List[Dict]:
        service_logger.info("Starting fetch all departments process")
        admin = self.auth.get_current_user()
        query = self.db.session.query(Department).join(Organization).filter(
            Organization.acronym == admin.organization.acronym
        )

        if filters:
            for column, value in filters.items():
                if hasattr(Department, column) and value is not None:
                    query = query.filter(getattr(Department, column).ilike(f'%{value}%'))

        result = [{
                'id': dept.id,
                'name': dept.name,
                "utility":dept.utility,
                'organization': dept.organization.name
            } for dept in query.all()]
        service_logger.info(f"Fetched departments: {result}")
        return result

    def fetch_one(self, name: str) -> Department:
        """Fetches a department by name

        Args:
            name (str): The name to search with

        Returns:
            Department: The found department

        Raises:
            NotFoundError: If the department is not found
        """
        service_logger.info(f"Starting fetch department process for name: {name}")
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Fetching department for organization: {organization_acronym}")

        department = self.db.session.query(Department).join(Organization).filter(
            Organization.acronym == organization_acronym,
            Department.name == name
        ).first()

        if department is None:
            raise NotFoundError("Department not found")
        
        service_logger.info(f"Fetched department: {department}")
        return department
    
    def update(self, name: str, request_data: Dict[str, Any]) -> Department:
        """Updates an existing department

        Args:
            name (str): The name of the department to update
            request_data (dict): The data to update the department with

        Returns:
            Department: The updated department

        Raises:
            NotFoundError: If the department to update is not found
        """
        service_logger.info(f"Starting update department process for name: {name}")
        schema_data = department_schema.load(request_data)
        department = self.fetch_one(name=name)

        for data in schema_data.items():
            setattr(department, *data)
        
        self.db.session.commit()
        service_logger.info(f"Updated department: {department}")
        return department
    
    def delete(self, name: str) -> None:
        """Deletes a department by name

        Args:
            name (str): The name of the department to delete

        Raises:
            NotFoundError: If the department to delete is not found
        """
        service_logger.info(f"Starting delete department process for name: {name}")
        department = self.fetch_one(name=name)
        if department is None:
            raise NotFoundError("Department not found")
        self.db.session.delete(department)
        self.db.session.commit()
        service_logger.info(f"Deleted department: {department}")


#fetch all the student in its organization, by department etc

class SessionMangement():
    def __init__(self):
        self.model = Session()
        self.db = db
        self.admin = User
        self.auth = AuthService(model=self.admin)
    
    def create(self, request_data: Dict[str, Any]):
        schema_data = session_schema.load(request_data)
        admin = self.auth.get_current_user()
        
        #getting the organization acronym for the admin
        organization_acronym = admin.organization.acronym
        organization_instance = self.db.session.query(Organization).filter_by(acronym=organization_acronym).first()
        if not organization_instance:
            raise NotFoundError("Organization not found")

        #linking the department to the organization
        schema_data["organization"] = organization_instance
        existing_session = self.db.session.query(Session).join(Organization).filter(
            Session.name == schema_data["name"],
            Organization.acronym == organization_acronym,
            Session.is_active == True
        ).first()
        if existing_session:
            raise AlreadyExistsError("An active session with this name already exists for the organization")
        schema_data["is_active"] = True
        service_logger.info(f"Creating session for organization: {organization_acronym}")
        
        service_logger.info(f"final data: {schema_data}")
        session = Session(**schema_data)
        self.db.session.add(session)
        self.db.session.commit()
        service_logger.info(f"Created session: {session}")
        return session
    
    def close_session(self, session_name: str):
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        session = self.db.session.query(Session).join(Organization).filter(
            Session.name == session_name,
            Organization.acronym == organization_acronym,
            Session.is_active == True
        ).first()
        if not session:
            raise NotFoundError("Session not found")
        session.is_active = False
        self.db.session.commit()
        service_logger.info(f"Closed session: {session}")

    def auto_close_sessions(self):
        current_time = datetime.now(datetime.timezone.utc).date()
        sessions_to_close = self.db.session.query(Session).filter(
            Session.end_date <= current_time,
            Session.is_active == True
        ).all()
        
        for session in sessions_to_close:
            session.is_active = False
            service_logger.info(f"Auto-closed session: {session}")
        
        self.db.session.commit()
    
    def fetch_all(self, **filters: Optional[Any]):
        admin = self.auth.get_current_user()
        query = self.db.session.query(Session).join(Organization).filter(
            Organization.acronym == admin.organization.acronym
        )

        if filters:
            for column, value in filters.items():
                if hasattr(Session, column) and value is not None:
                    query = query.filter(getattr(Session, column).ilike(f'%{value}%'))

        result = query.all()
        service_logger.info(f"Fetched sessions: {result}")
        return result
    
    def fetch_one(self, session_name: str):
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        session = self.db.session.query(Session).join(Organization).filter(
            Session.name == session_name,
            Organization.acronym == organization_acronym
        ).first()
        service_logger.info(f"Fetched session: {session}")
        return session
    
    def fetch_all_active_session(self):
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        sessions = self.db.session.query(Session).join(Organization).filter(
            Organization.acronym == organization_acronym,
            Session.is_active == True
        )
        result = [{
            'id': session.id,
            'name': session.name,
            'start_date': session.start_date,
            'end_date': session.end_date
            
        } for session in sessions.all()]
        service_logger.info(f"Fetched active sessions: {result}")
        return result

class OrganizationPaymentItems():
    def __init__(self):
        self.auth = AuthService(model=User)
    def fetch_all_payment_items_by_departments(self):
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Fetching payment items for all departments in organization: {organization_acronym}")

        query = self.db.session.query(PaymentItem).join(Department).join(Organization).filter(
            Organization.acronym == organization_acronym
        )

        result = [{
            'id': item.id,
            'name': item.name,
            'amount': item.amount,
            'academic_session': item.academic_session.name,
            'level': item.level.name,
            'department': item.department.name,
            'organization': item.organization.name
        } for item in query.all()]
        service_logger.info(f"Fetched payment items: {result}")
        return result
    
    
    def fetch_departments_with_successful_payment(self):
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Fetching departments with successful payment for organization: {organization_acronym}")

        query = self.db.session.query(Department, func.count(Payment.id).label('payment_count')).join(PaymentItem).join(Payment).filter(
            Payment.status == TransactionStatus.SUCCESS.value,
            PaymentItem.department_id == Department.id,
            Department.organization_id == Organization.id,
            Organization.acronym == organization_acronym
        ).group_by(Department)

        result = [{
            'id': department.id,
            'name': department.name,
            'payment_count': payment_count
        } for department, payment_count in query.all()]
        service_logger.info(f"Fetched departments with successful payment: {result}")
        return result
    
    
    def fetch_departments_with_total_successful_payment(self):
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Fetching departments with total successful payment for organization: {organization_acronym}")

        query = self.db.session.query(Department, func.sum(Payment.amount).label('total_amount')).join(PaymentItem).join(Payment).filter(
            Payment.status == TransactionStatus.SUCCESS.value,
            PaymentItem.department_id == Department.id,
            Department.organization_id == Organization.id,
            Organization.acronym == organization_acronym
        ).group_by(Department)

        result = [{
            'id': department.id,
            'name': department.name,
            'total_amount': total_amount
        } for department, total_amount in query.all()]
        service_logger.info(f"Fetched departments with total successful payment: {result}")
        return result
    

class ClearanceItem(BaseService):
    def create(self, request_data):
        pass 
    
    
    #fetch all the payment items by students in the organization    
    #fetch all the payment items by session, grouped by department
    #fetch all the payment items by session
    #fetch all departments, with its subadmin, students
    
    #the department  you are getting from the current user, if an admin logs in, it is going to evaluate to none, an error occurs
    #if the admin logs in, pass in a department param that will be able to fetch for the department, if the subadmin is logged in, use his department