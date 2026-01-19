from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from src.auth.service import verify_password, password_hash
from src.model import Department, Organization, PassPorts, SchoolSession, User, Role_Enum, Level_Enum
from src.base.exception import (
    NotFoundError,
    AlreadyExistsError,
    InvalidEmailPassword,
    ServerError,
    AuthorizationError

)
from src.schema.user import CreateUser
from flask_jwt_extended import get_jwt_identity
from src.auth.schema import Login
from src.schema.user import UpdatePassword
from src.utils.config import config
from src.utils.log import setup_logger
logger = setup_logger(__name__, "user_service.log")

class UserService():
    def __init__(self, db:Session):
        self.db = db 
    
    def create_user(self, user_data:CreateUser):
        user = self.check_if_user_exist_by_email(user_data.email)
        if user:
            raise AlreadyExistsError()
        #other checks
        
        new_user = User(
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            middlename=user_data.middlename,
            email=user_data.email,
            matric_number=user_data.matric_number,
            phone_number=user_data.phone_number,
            level=Level_Enum(user_data.level) if user_data.level is not None else None,
            password_hash=password_hash(user_data.password),
            role=user_data.role,
            organization_id=user_data.organization_id,
            faculty_id=user_data.faculty_id,
            department_id=user_data.department_id,
            clearance_point_id=user_data.clearance_point_id
        )
        self.db.add(new_user)
        self.db.commit()
        return new_user
    
    def check_if_user_exist_by_email(self, email:str):
        stmt = self.db.execute(
            select(User).where(
                User.email == email
            )
    )
        user = stmt.scalar_one_or_none()
        return user
    
    def check_if_user_exist_by_id(self, id:str):
        stmt = self.db.execute(
            select(User).where(
                User.id == id
            )
    )
        user = stmt.scalar_one_or_none()
        return user
    

    def fetch_all_users(self):
        stmt = select(User) 
        users = self.db.execute(stmt).scalars().all()
        return users
    
    def check_if_user_exist_by_matric_number(self, matric_num:str):
        stmt = self.db.execute(
            select(User).where(
                User.matric_number == matric_num
            )
    )
        user = stmt.scalar_one_or_none()
        return user
    
    
    def authenticate_user(self, user_data: Login):
        try:
            user = None

            # Try to find user by email if provided
            if user_data.email:
                user = self.check_if_user_exist_by_email(user_data.email)
                if user:
                    logger.debug(f"user found by email: {user.email}")

            # If not found, try matric_number
            if not user and user_data.matric_number:
                user = self.check_if_user_exist_by_matric_number(user_data.matric_number)
                if user:
                    logger.debug(f"user found by matric: {user.matric_number}")

            # Handle not found
            if not user:
                identifier = user_data.email or user_data.matric_number or "unknown"
                logger.warning(
                    f"Authentication failed: User with identifier '{identifier}' does not exist."
                )
                raise NotFoundError(
                    f"User with identifier '{identifier}' does not exist."
                )

            # verify password
            if not verify_password(user_data.password, user.password):
                logger.warning(
                    f"Authentication failed: Invalid password for user {user.id}."
                )
                raise InvalidEmailPassword()

            # do further authentication

            # prepare jwt payload
            jwt_payload = {"user_id": str(user.id), "role": user.role.value}
            logger.info(f"Authentication successful for user {user.id}.")
            return jwt_payload
        except SQLAlchemyError as e:
            logger.error(f"Database error during authentication: {e}")
            raise ServerError()
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")
            raise ServerError()
    
    def update_password(self, user_data:UpdatePassword):
        try:
            logger.info(f"Attempting to update password for user ID: {user_data.user_id}")
            user = self.check_if_user_exist_by_id(user_data.user_id)
            if not user:
                logger.warning(f"Password update failed: User with ID {user_data.user_id} not found")
                raise NotFoundError()
            if user.role not in [Role_Enum.ADMIN, Role_Enum.SUB_ADMIN, Role_Enum.STUDENT, Role_Enum.SUPER_ADMIN]:
                logger.warning(f"Password update failed: User {user_data.user_id} with role {user.role} not authorized")
                raise AuthorizationError()  # only these roles can change password. Other roles have restrictions
            old_password_hash = password_hash(user_data.old_password)
            if user.password != old_password_hash:
                logger.warning(f"Password update failed: Invalid old password for user {user_data.user_id}")
                raise InvalidEmailPassword()
            if user_data.new_password != user_data.confirm_new_password:
                logger.warning(f"Password update failed: New password confirmation mismatch for user {user_data.user_id}")
                raise InvalidEmailPassword()
            

            new_password_hash = password_hash(user_data.new_password)
            user.password = new_password_hash
            self.db.add(user)
            self.db.commit()
            logger.info(f"Password updated successfully for user ID: {user_data.user_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error during password update for user {user_data.user_id}: {e}")
            self.db.rollback()
            raise ServerError()
        except (NotFoundError, AuthorizationError, InvalidEmailPassword):
            # Re-raise custom exceptions without logging again as they're already logged
            raise
        except Exception as e:
            logger.error(f"Unexpected error during password update for user {user_data.user_id}: {e}")
            self.db.rollback()
            raise ServerError()
        
    def reset_password():
        pass 
    
    def business_logic_to_create_users(self, current_user:User, user_data:CreateUser):
        try:
            logger.info(f"Starting user creation process for role {user_data.role} by user {current_user.id}")

            # Handle organization validation - ensure admin can only create users in their organization
            organization_id = current_user.organization_id
            logger.debug(f"Loading organization {organization_id} with departments")
            stmt = select(Organization).options(selectinload(Organization.departments)).where(Organization.id == organization_id)
            organization = self.db.execute(stmt).scalar_one_or_none()
            if not organization:
                logger.error(f"Organization {organization_id} not found for user {current_user.id}")
                return None

            logger.debug(f"Organization {organization.name} loaded successfully")

            # Handle department and level logic
            department = None
            faculty_id = None
            level = user_data.level

            if current_user.department_id and user_data.role == Role_Enum.STUDENT:
                logger.debug("Processing department logic for student creation")
                # Since we already loaded organization with departments, find the department from the loaded collection
                department = next((dept for dept in organization.departments if dept.id == current_user.department_id), None)
                if not department:
                    logger.error(f"Department {current_user.department_id} not found in organization {organization.name}")
                    return None
                faculty_id = department.faculty_id
                logger.debug(f"Department {department.name} and faculty {faculty_id} assigned")

                # TODO: Automatic level calculation based on matric number - commented out for now
                # Keeping for future implementation when needed
                # Calculate level based on matric number for students
                # if user_data.matric_number:
                #     try:
                #         logger.debug(f"Calculating level for matric number {user_data.matric_number}")
                #         code = user_data.matric_number.split("/")
                #         if len(code) >= 2:
                #             year = 2000 + int(code[0])
                #             current_year = self.db.execute(
                #                 select(SchoolSession).where(SchoolSession.is_active == True, SchoolSession.organization_id == organization.id)
                #             ).scalar_one_or_none()
                #             if current_year:
                #                 years = current_year.end_year - year
                #                 level = years * 100 if years >= 0 else None
                #                 logger.debug(f"Calculated level: {level} (years: {years})")
                #             else:
                #                 logger.warning(f"No active session found for organization {organization.id}")
                #     except (ValueError, IndexError) as e:
                #         logger.warning(f"Failed to calculate level from matric number {user_data.matric_number}: {e}")
                #         # Keep original level if calculation fails

            # Prepare updated user data with computed fields
            updated_user_data = CreateUser(
                firstname=user_data.firstname,
                lastname=user_data.lastname,
                middlename=user_data.middlename,
                email=user_data.email,
                matric_number=user_data.matric_number,
                phone_number=user_data.phone_number,
                level=level,
                password=user_data.password,
                role=user_data.role,
                organization_id=organization.id,
                faculty_id=faculty_id,
                department_id=department.id if department else user_data.department_id,
                clearance_point_id=user_data.clearance_point_id
            )

            logger.info(f"User data prepared, calling create_user method for {user_data.email}")

            # Reuse the existing create_user method
            created_user = self.create_user(updated_user_data)
            logger.info(f"User {created_user.id} ({created_user.email}) created successfully")
            return created_user

        except SQLAlchemyError as e:
            logger.error(f"Database error during user creation: {e}")
            self.db.rollback()
            return None
        except Exception as e:
            logger.error(f"Unexpected error during user creation: {e}")
            self.db.rollback()
            return None
        
        
            
    
    def get_current_user(self):
        user_id = get_jwt_identity()
        if not user_id:
            return None
        user = self.check_if_user_exist_by_id(user_id)
        if not user:
            raise NotFoundError(f"{user_id} not found")
        return user
