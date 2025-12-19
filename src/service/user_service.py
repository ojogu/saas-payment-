from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from auth.service import verify_password
from src.model import Department, Organization, PassPorts, Session, User, db
from src.base.exception import (
    NotFoundError,
    AlreadyExistsError,
    InvalidEmailPassword,
    ServerError
)
from src.auth.schema import Login
from src.utils.log import setup_logger

logger = setup_logger(__name__, "user_service.log")

class UserService():
    def __init__(self, db: Session):
        self.db = db 
        
    
    def check_if_user_exist_by_email(self, email:str):
        stmt = db.execute(
            select(User).where(
                User.email == email
            )
    )
        user = stmt.scalar_one_or_none()
        return user
    

    def check_if_user_exist_by_matric_number(self, matric_num:str):
        stmt = db.execute(
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
