from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from src.auth.service import verify_password, password_hash
from src.model import Department, Organization, PassPorts, User, Role_Enum
from src.base.exception import (
    NotFoundError,
    AlreadyExistsError,
    InvalidEmailPassword,
    ServerError,
    AuthorizationError
    
)
from flask_jwt_extended import get_jwt_identity
from src.auth.schema import Login
from src.schema.user import UpdatePassword
from src.utils.log import setup_logger
logger = setup_logger(__name__, "user_service.log")

class UserService():
    def __init__(self, db:Session):
        self.db = db 
    
    def create_user(self):
        pass 
    
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
    
    def get_current_user(self):
        user_id = get_jwt_identity() 
        if not user_id:
            
            return 
        user = self.check_if_user_exist_by_id(user_id)
        if not user:
            raise NotFoundError(f"{user_id} not found")
        return user
