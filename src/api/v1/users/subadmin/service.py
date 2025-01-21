#this is the subadmin class that manages the platform fo students, it onboards student users, add payment items etc
import os
import requests
from api.base.service import BaseService
import logging
from utils.dependency import db
from api.v1.users .model import User, Role, Level, Session, PaymentItem, Department, Payment, User, TransactionStatus, RoleEnum, Organization
from api.v1.auth.service import AuthService
from utils.exception import InUseError, NotFoundError, AlreadyExistsError
from api.v1.users.students.schema import student_schema
from typing import Any, Optional, List, Dict
import json
from utils.util import get_env_value
from .schema import payment_item_schema
import pandas as pd

#setup logging
service_logger = logging.getLogger(__name__)
service_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/service.log')
file_handler.setFormatter(formatter)
service_logger.addHandler(file_handler)



class StudentManagement(BaseService):
    def __init__(self):
        self.model = User
        self.db = db
        self.auth = AuthService(model=self.model)
    def create(self, request_data: Dict[str, Any]) -> User:
        service_logger.info("Starting student creation process")
        service_logger.info(f"request_data, {request_data}")
        schema_data = student_schema.load(request_data)
        service_logger
        clean_mail = self.auth.clean_email(schema_data["email"])
        role_name = "STUDENT"

        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Creating student for organization: {organization_acronym}")

        department_name = schema_data["department"]
        department_instance = self.db.session.query(Department).join(Organization).filter(
            Organization.acronym == organization_acronym,
            Department.name == department_name
            ).first()
        if not department_instance:
            raise NotFoundError("Department not found")
        
        #linking department
        schema_data["department"] = department_instance

        role_instance = self.db.session.query(Role).filter_by(name=role_name).first()
        service_logger.info(f"Role query result: {role_instance}")
        organization_instance = self.db.session.query(Organization).filter_by(acronym=organization_acronym).first()
        service_logger.info(f"Organization query result: {organization_instance}")
        if not role_instance or not organization_instance:
            raise NotFoundError("Role or organization not found")

        existing_student = self.db.session.query(self.model).filter_by(email=clean_mail).first()
        if existing_student:
                raise InUseError("Student already exists")
            
        #linking role and organization
        schema_data["role"] = role_instance
        schema_data["organization"] = organization_instance
        
        level = schema_data["level"]
        # service_logger.info(level)
        level_instance = self.db.session.query(Level).filter(Level.name == level).first()
        
        schema_data["level"] = level_instance
        
        #hashing password
        default_password = self.auth.default_password()
        schema_data['password'] = self.auth.hash_password(default_password)
        service_logger.info(f"About to commit user: {schema_data}")
        
        
        student = User(**schema_data)
        service_logger.info(f"About to commit user: {student}")
        self.db.session.add(student)
        self.db.session.commit()
        service_logger.info(f"Created user: {student}")
        return student
    
    def bulk_creation(self, excel_file):
        service_logger.info("Starting bulk student creation process")
        df = pd.read_excel(excel_file)
        service_logger.info(f"Loaded Excel file with {len(df)} rows")
        for index, row in df.iterrows():
            student_data = {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "department": row["department"].title(),
                "email": row["email"],
                "level": str(row["level"]),
                "matric_number": row["matric_number"],
                "phone": str(row["phone"]),
                "campus": row["campus"],
                "faculty": row["faculty"],
                "residential_address": row["residential_address"],
            }
            try:
                service_logger.info(f"Creating student {index + 1}/{len(df)}: {student_data['email']}")
                self.create(request_data=student_data)
                service_logger.info(f"Successfully created student: {student_data['email']}")
            except AlreadyExistsError as e:
                service_logger.error(f"Failed to create student {student_data['email']}: {e}")


    def fetch_all(self, **filters: Optional[Any]) -> List[Dict]:
        # Fetch all the students in the current user's organization and department
        service_logger.info("Starting fetch all students process")
        current_user = self.auth.get_current_user()
        service_logger.info(current_user)

        # Check if user is an admin 
        is_admin = current_user.role.name == RoleEnum.ADMIN

        if is_admin:
            service_logger.info("Fetching all students in the database (admin view)")
            query = self.db.session.query(self.model).join(Role).filter(
                Role.name == RoleEnum.STUDENT
            )
        else:
            service_logger.info("Fetching all students in the subadmin department")
            organization_acronym = current_user.organization.acronym
            department_name = current_user.department.name
            service_logger.info(f"Fetching all students for organization: {organization_acronym} and department: {department_name}")

            query = self.db.session.query(self.model).join(Role).join(Organization).join(Department).filter(
                    Role.name == "STUDENT",
                    Organization.acronym == organization_acronym,
                    Department.name == department_name
                )
        
        students = query.all()
        service_logger.info(f"Fetched students: {[(student.first_name, student.last_name, student.matric_number) for student in students]}")
        return query.all()
    def fetch_one(self, matric_number: str) -> User:
        service_logger.info(f"Starting fetch student process for matric number: {matric_number}")
        current_user = self.auth.get_current_user()
        is_admin = current_user.role.name == RoleEnum.ADMIN
        
        # Start with base query filtering by matric number first
        query = self.db.session.query(self.model).filter(self.model.matric_number == matric_number)

        # Then add role join and other filters
        query = query.join(Role)

        if is_admin:
            service_logger.info("Fetching student as admin")
            query = query.filter(Role.name == RoleEnum.STUDENT)
        else:
            service_logger.info("Fetching student as subadmin")
            organization_acronym = current_user.organization.acronym
            department_name = current_user.department.name
            service_logger.info(f"Fetching student for organization: {organization_acronym} and department: {department_name}")
            
            query = query.join(Organization).join(Department).filter(
                Role.name == RoleEnum.STUDENT,
                Organization.acronym == organization_acronym,
                Department.name == department_name
            )

        user = query.first()
        service_logger.info(f"Fetched student: {user}")
        return user

    def update(self, matric_number: str, request_data: Dict[str, Any]) -> User:
        service_logger.info(f"Starting update student process for matric number: {matric_number}")
        sub_admin = self.auth.get_current_user()
        organization_acronym = sub_admin.organization.acronym
        service_logger.info(f"Updating student for organization: {organization_acronym}")

        user = self.fetch_one(matric_number)

        if not user:
            raise NotFoundError("Student not found")

        schema_data = student_schema.load(request_data, partial=True)

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

    def delete(self, matric_number: str) -> None:
        service_logger.info(f"Starting delete student process for matric number: {matric_number}")
        admin = self.auth.get_current_user()
        organization_acronym = admin.organization.acronym
        service_logger.info(f"Deleting student for organization: {organization_acronym}")

        user = self.fetch_one(matric_number)
        if not user:
            raise NotFoundError("Student not found")

        self.db.session.delete(user)
        self.db.session.commit()
        service_logger.info(f"Deleted student: {user}")
        # service_logger.info(f"Deleted student: {user}")


class PaymentItemManagment(BaseService):
    def __init__(self):
        self.payment_item = PaymentItem()
        self.db = db
        self.admin = AuthService(model=User)
        self.paystack_secret_key = "sk_test_5549e0f982fe151fd1f2d76287d841a5ed9fd11a"
        self.model = PaymentItem
    def get_bank_code(self, name):
        script_dir=os.path.dirname(os.path.abspath(__file__))

        file_path=os.path.join(script_dir,'banks.json')

        f=open(file_path,'r')
        data=f.read()
        banks = json.loads(data)
        for bank in banks['data']:
            if bank['name'].lower() == name.lower():
                return {
                    'name': bank['name'],
                    'code': bank['code'],
                    'slug': bank['slug'],
                    'longcode': bank.get('longcode', None),
                    'country': bank['country'],
                    'currency': bank['currency'],
                    'type': bank['type'],
                }

        raise NotFoundError("Bank not found")
        
    def create_account_details(self, **kwargs):
        payload = kwargs

        headers = {
            "Authorization": f"Bearer {self.paystack_secret_key}",
            "Content-Type": "application/json"
        }
        service_logger.info(self.paystack_secret_key)
        response = requests.post("https://api.paystack.co/subaccount", json=payload, headers=headers)
        service_logger.info(f"Payment initialized: {response.json()}") 
        return response.json()
    
    def create(self, request_data):
        parsed_data = payment_item_schema.load(request_data)
        service_logger.info(f"parsed_data: {parsed_data}")

        user = self.admin.get_current_user()
        if user.role.name == RoleEnum.SUBADMIN:
            department_name = user.department.name
            organization_acronym = user.organization.acronym
            service_logger.info(f"Creating payment item for organization: {organization_acronym}, department: {department_name}")
        else:
            organization_acronym = user.organization.acronym
            department_name = parsed_data.get("department")
            service_logger.info(f"Creating payment item for organization: {organization_acronym}, department: {department_name}")
        try:
            bank_details = self.get_bank_code(parsed_data["bank_name"])
            bank_code = bank_details['code']
            service_logger.info(bank_code)
        except NotFoundError as e:
            service_logger.error(f"Bank not found: {parsed_data['bank_name']}")
            return "not found error"
        
        academic_session = parsed_data["academic_session"]
        level = parsed_data["level"]
        service_logger.info(f"Creating payment item for organization: {organization_acronym}, department: {department_name}, level: {level}, session: {academic_session}")

        department_instance = self.db.session.query(Department).join(Organization).filter(
            Organization.acronym == organization_acronym,
            Department.name == department_name
        ).first()
        if not department_instance:
            raise NotFoundError("Department not found")

        session_instance = self.db.session.query(Session).join(Organization).filter(
            Organization.acronym == organization_acronym,
            Session.is_active == True,
            Session.name == academic_session
        ).first()
        service_logger.info(f"session_instance: {session_instance}")
        if not session_instance:
            raise InUseError("Cannot register payment item for an inactive session")

        organization_instance = self.db.session.query(Organization).filter(Organization.acronym == organization_acronym).first()

        level_instance = self.db.session.query(Level).filter(Level.name == level).first()


        
        parsed_data["percentage_charge"] = str(parsed_data["percentage_charge"])
        parsed_data["organization"] = organization_instance
        parsed_data["department"] = department_instance
        parsed_data["level"] = level_instance
        parsed_data["academic_session"] = session_instance
        service_logger.info(f"finalized parsed_data: {parsed_data}")
        
        business_name = f"{department_name} - {parsed_data['name']}"
        account_data = {
            "business_name": business_name,
            "settlement_bank": bank_code, 
            "account_number": parsed_data["account_number"],
            "percentage_charge" : parsed_data["percentage_charge"],
            
        }
        service_logger.info(f"account data: {account_data}")
        account_details = self.create_account_details(**account_data)
        parsed_data["business_name"] = account_details["data"]["business_name"]
        parsed_data["bank_name"] = account_details["data"]["settlement_bank"]
        parsed_data["account_name"] = account_details["data"]["account_name"]
        parsed_data["subaccount_code"] = account_details["data"]["subaccount_code"]
        parsed_data["account_number"] = account_details["data"]["account_number"]
        
        payment_item = PaymentItem(**parsed_data)
        service_logger.info(f"payment_item: {payment_item}")
        self.db.session.add(payment_item)
        self.db.session.commit()
        service_logger.info("Created payment item")
    
    def fetch_all(self, **filters: Optional[Any]):
        service_logger.info("Starting fetch all payment items process")
        current_user = self.admin.get_current_user()
        service_logger.info(current_user)

        # Check if user is an admin
        is_admin = current_user.role.name == RoleEnum.ADMIN

        if is_admin:
            service_logger.info("Fetching all payment items in the database (admin view)")
            query = self.db.session.query(self.model).join(Department)
        else:
            service_logger.info("Fetching all payment items in the subadmin department")
            organization_acronym = current_user.organization.acronym
            department_name = current_user.department.name
            service_logger.info(f"Fetching all payment items for organization: {organization_acronym} and department: {department_name}")

            query = self.db.session.query(self.model).join(Department).join(Organization).filter(
                Organization.acronym == organization_acronym,
                Department.name == department_name
            )

        if filters:
            for column, value in filters.items():
                if hasattr(self.model, column) and value is not None:
                    query = query.filter(getattr(self.model, column) == value)

        result = [{
            'id': items.id,
            'name': items.name,
            'amount': items.amount,
            'academic_session': items.academic_session.name,
            'level': items.level.name,
            'department': items.department.name,
            'organization': items.organization.name,
            'bank_name': items.bank_name,
            'account_name': items.account_name,
            'account_number': items.account_number,
        } for items in query.all()]
        service_logger.info(f"Fetched payment items: {result}")
        return result
    
    def fetch_one(self, name: str, level: str, department_name: str = None) -> PaymentItem:
        service_logger.info(f"Starting fetch payment item process")
        current_user = self.admin.get_current_user()
        is_admin = current_user.role.name == RoleEnum.ADMIN

        if is_admin and department_name:
            department = db.session.query(Department).filter(Department.name == department_name).first()
            if not department:
                raise NotFoundError("Department not found")
        else:
            department = current_user.department

        service_logger.info(f"Fetching payment item for organization: {current_user.organization.acronym} and for department: {department.name if department else 'Not found'}")

        query = (
            db.session.query(PaymentItem)
            .join(Department, PaymentItem.department_id == Department.id)
            .join(Level, PaymentItem.level_id == Level.id)
            .join(Organization, Department.organization_id == Organization.id)
            .filter(
                PaymentItem.name.ilike(f"%{name}%"),
                Organization.acronym == current_user.organization.acronym,
                Department.name == department.name,
                Level.name.ilike(f"%{level}%"),
            )
            .options(
                db.joinedload(PaymentItem.organization),  # Eagerly load `organization`
                db.joinedload(PaymentItem.department),    # Eagerly load `department`
                db.joinedload(PaymentItem.level),         # Eagerly load `level`
            )
        )
        result = query.first()
        if not result:
            service_logger(
                f"No payment item '{name}' found for organization: {current_user.organization.acronym}, "
                f"department: {department.name if department else 'Not found'}, level: {level}"
            )
            raise NotFoundError("Payment item not found")
        return result

    def update(self, name=None, level=None, request_data=None):
        service_logger.info(f"Starting update payment item process")
        subadmin = self.admin.get_current_user()
        organization_acronym = subadmin.organization.acronym
        department = subadmin.department.name
        service_logger.info(f"Updating payment item for organization: {organization_acronym} and for department: {department}")

        payment_item = self.fetch_one(name, level)
        if not payment_item:
            raise NotFoundError("Payment item not found")

        parsed_data = payment_item_schema.load(request_data)
        for key, value in parsed_data.items():
            setattr(payment_item, key, value)

        self.db.session.commit()
        return payment_item

    def delete(self, name=None, level=None, department_name=None):
        service_logger.info(f"Starting delete payment item process")
        current_user = self.admin.get_current_user()
        organization_acronym = current_user.organization.acronym

        if current_user.role.name == RoleEnum.ADMIN:
            if not department_name:
                raise ValueError("Department name must be provided for admins")
            department = self.db.session.query(Department).filter_by(name=department_name).first()
        else:
            department = current_user.department

        if not department:
            raise NotFoundError("Department not found")

        service_logger.info(f"Deleting payment item for organization: {organization_acronym} and for department: {department.name}")

        payment_item = self.fetch_one(name, level, department_name=department.name)
        if not payment_item:
            raise NotFoundError("Payment item not found")

        self.db.session.delete(payment_item)
        self.db.session.commit()
        service_logger.info(f"Deleted payment item: {payment_item}")
        
    def fetch_all_by_level(self, level):
        service_logger.info(f"Starting fetch payment items by level process")
        current_user = self.admin.get_current_user()
        organization_acronym = current_user.organization.acronym

        if current_user.role.name == RoleEnum.ADMIN:
            service_logger.info(f"Fetching payment items for organization: {organization_acronym}")
            query = self.db.session.query(PaymentItem).join(Organization).filter(
                Organization.acronym == organization_acronym,
                PaymentItem.level == level
            )
        else:
            department = current_user.department.name
            service_logger.info(f"Fetching payment items for organization: {organization_acronym} and for department: {department}")

            query = self.db.session.query(PaymentItem).join(Organization).join(Department).filter(
                Organization.acronym == organization_acronym,
                Department.name == department,
                PaymentItem.level == level
            )

        result = query.all()
        return result
    
    def fetch_all_by_session(self, session):
        service_logger.info(f"Starting fetch payment items by session process")
        subadmin = self.admin.get_current_user()
        organization_acronym = subadmin.organization.acronym
        department = subadmin.department.name
        service_logger.info(f"Fetching payment items for organization: {organization_acronym} and for department: {department}")

        query = self.db.session.query(PaymentItem).join(Organization).join(Department).filter(
            Organization.acronym == organization_acronym,
            Department.name == department,
            PaymentItem.session == session
        )

        result = query.all()
        return result


class PaymentQuery():
    def __init__(self):
        self.db = db
        self.auth = AuthService(model=User)
        self.model = Payment
    
    def fetch_all_successful_payment(self):
        
        """
        Fetch all paid payment items for the current user's organization
        and for all departments if the user is an admin, otherwise
        fetch all paid payment items for the current user's department

        :return: A list of all paid payment items
        """
        service_logger.info(f"Starting fetch all paid items process")
        current_user = self.auth.get_current_user()

        if current_user.role.name == RoleEnum.ADMIN:
            service_logger.info(f"Fetching paid payment items for all departments")
            query = self.db.session.query(self.model).join(User).join(PaymentItem).filter(
                User.organization.has(acronym=current_user.organization.acronym),
                self.model.status == TransactionStatus.SUCCESSFUL.value
            )
        else:
            organization_acronym = current_user.organization.acronym
            department = current_user.department.name
            service_logger.info(f"Fetching paid payment items for organization: {organization_acronym} and for department: {department}")

            query = self.db.session.query(self.model).join(User).join(PaymentItem).join(Department).filter(
                Department.name == department,
                User.organization.has(acronym=organization_acronym),
                self.model.status == TransactionStatus.SUCCESSFUL.value
            )

        result = query.all()
        return result
    
    def fetch_pending_payment(self, department=None):
        """
        Fetch all pending payment items for the current user's organization
        and for all departments if the user is an admin, otherwise
        fetch all pending payment items for the current user's department

        If the user is an admin, the department name must be provided

        :param department: The name of the department to fetch payment items from
        :return: A list of all pending payment items
        """
        service_logger.info(f"Starting fetch all pending payment items process")
        subadmin = self.auth.get_current_user()
        organization_acronym = subadmin.organization.acronym
        if subadmin.role.name == RoleEnum.ADMIN:
            if department is None:
                raise ValueError("Admin must provide department name")
            service_logger.info(f"Fetching pending payment items for organization: {organization_acronym} and for department: {department}")
        else:
            department = subadmin.department.name
            service_logger.info(f"Fetching pending payment items for organization: {organization_acronym} and for department: {department}")

        query = self.db.session.query(self.model).join(User).join(PaymentItem).join(Department).filter(
            Department.name == department,
            User.organization.has(acronym=organization_acronym),
            self.model.status == TransactionStatus.PENDING.value
        )
        result = query.all()
        return result
    
    
    def fetch_all_payment_made_in_department(self, department=None):
        """
        Fetch all payment made in a department

        If the user is an admin, the department name must be provided

        :param department: The name of the department to fetch payment items from
        :return: A list of all payment made in the department
        """
        service_logger.info(f"Starting fetch all payment made in department process")
        subadmin = self.auth.get_current_user()
        if subadmin.role.name == RoleEnum.ADMIN:
            organization_acronym = subadmin.organization.acronym
            if department is None:
                raise ValueError("Admin must provide department name")
            service_logger.info(f"Fetching all payment made in department: {department}")
        else:
            organization_acronym = subadmin.organization.acronym
            department = subadmin.department.name
            service_logger.info(f"Fetching all payment made in department: {department}")

        query = self.db.session.query(User.first_name, User.last_name, PaymentItem.name, Payment.amount).join(PaymentItem).join(User).join(Department).filter(
            Department.name == department,
            User.organization.has(acronym=organization_acronym)
        )
        result = query.all()
        return result

class ClearanceCertificate():
    pass 