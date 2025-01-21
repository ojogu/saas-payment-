# This is the service module for the auth, contains auth specific methods like login, password hashing, current users etc

from utils.dependency import db
from utils.exception import NotFoundError, AlreadyExistsError, InvalidEmailPassword, BadRequest
import utils.dependency
import logging
from .schema import super_admin_schema, password_reset_schema
from flask_jwt_extended import get_jwt_identity 

# Setup logging
auth_logger = logging.getLogger(__name__)
auth_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/auth.log')
file_handler.setFormatter(formatter)
auth_logger.addHandler(file_handler)

class AuthService():
    """
    This is the service module for the auth, contains auth specific methods like login, password hashing, current users etc.
    """
    def __init__(self, model):
        """
        Initializes the service with a model.

        Args:
            model: the model to use for the service
        """
        self.model = model
        self.db = db
        
    @classmethod
    def clean_email(cls, email: str) -> str:
        """
        Cleans an email by stripping and lower casing it.

        Args:
            email (str): the email to clean

        Returns:
            str: the cleaned email
        """
        return email.strip().lower()
    
    def test(self):
        return "hello"
    
    def create(self, request_data: dict):
        """
        Creates a new user.

        Args:
            request_data (dict): the data to create the user with

        Returns:
            The created user
        """
        schema_data = super_admin_schema.load(request_data)
        clean_mail = self.clean_email(schema_data["email"])
        # Checks for an existing user
        existing_admin = self.db.session.query(self.model).filter_by(email=clean_mail).first()
        if existing_admin:
            raise AlreadyExistsError("User already exists")
        
        # If the request data validates, hashes the password
        schema_data['password'] = self.hash_password(schema_data['password'])
        # Stores the user data in the database
        admin = self.model(**schema_data)
        self.db.session.add(admin)
        self.db.session.commit()
        self.db.session.refresh(admin)
        auth_logger.info(f"Created user: {admin}")
        return admin
    
    def authenticate_user(self, user_email: str, password: str):
        """
        Authenticates a user with the given email and password.

        Args:
            user_email (str): the email of the user to authenticate
            password (str): the password of the user to authenticate

        Returns:
            The authenticated user
        """
        query = self.db.session.query(self.model)
        user = query.filter_by(email=user_email).first()
        if user is None:
            auth_logger.info("User not found")
            raise NotFoundError("User not found")
        
        auth_logger.info(f"User found: {user}")
        if not self.verify_password(hashed_password=user.password, password=password):
            raise InvalidEmailPassword("Invalid password or email")
        if user:
            auth_logger.info("User authenticated")
        return user
    
    def default_password(self) -> str:
        """
        Returns the default password.

        Returns:
            str: the default password
        """
        return "default@123"
    
    def hash_password(self, password: str) -> str:
        """
        Hashes a password.

        Args:
            password (str): the password to hash

        Returns:
            str: the hashed password
        """
        return utils.dependency.bcrypt.generate_password_hash(password).decode('utf-8')
    
    def verify_password(self, hashed_password: str, password: str) -> bool:
        """
        Verifies a password with a given hashed password.

        Args:
            hashed_password (str): the hashed password to verify with
            password (str): the password to verify

        Returns:
            bool: whether the password is valid or not
        """
        return utils.dependency.bcrypt.check_password_hash(hashed_password, password)
    
    def change_password(self, request_data):
        schema_data = password_reset_schema.load(request_data)
        user = self.authenticate_user(email=schema_data['email'], password=schema_data['old_password'])

        if schema_data['new_password'] != schema_data['confirm_password']:
            raise BadRequest('Passwords do not match')

        if schema_data['new_password'] == schema_data['old_password']:
            raise BadRequest('New password cannot be the same as the old password')

        user.password = self.hash_password(schema_data['new_password'])
        self.db.session.commit()

    def get_current_user(self):
        """
        Gets the current user.

        Returns:
            The current user
        """
        user_unique_id = get_jwt_identity()
        
        auth_logger.info(user_unique_id)
        query = self.db.session.query(self.model)
        # auth_logger.info(query)
        user = query.filter_by(entity_id=user_unique_id).first()
        auth_logger.info(f"User found: {user}")
        if user is None:
            auth_logger.error("User not found")
            raise NotFoundError("Not found")
        return user
