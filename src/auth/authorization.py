from functools import wraps
from flask import jsonify
from typing import List
from src.base.exception import AuthorizationError
from src.utils.log import setup_logger

logger = setup_logger(__name__, "authorization.log")


class RoleCheck:
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the user_service from kwargs (injected by dishka)
            user_service = kwargs.get('user_service')
            if not user_service:
                # Try to find it in args or assume it's injected
                # For now, assume it's passed as kwarg
                return jsonify({"message": "Authorization service not available"}), 500

            current_user = user_service.get_current_user()
            logger.info(f"Role check for user {current_user.id} with role {current_user.role.value} against required roles {self.required_roles}")

            user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)

            access = self.has_access(self.required_roles, [user_role])
            if access:
                logger.info(f"Access granted for user {current_user.id}")
                return func(*args, **kwargs)
            else:
                logger.warning(f"Access denied for user {current_user.id}: required roles {self.required_roles}, user role {user_role}")
                raise AuthorizationError(f"Access denied. Required roles: {self.required_roles}")

        return wrapper

    def has_access(self, required_roles: List[str], user_roles: List[str]) -> bool:
        # Ensure single string role is treated as a list
        if isinstance(user_roles, str):
            user_roles = [user_roles]

        if isinstance(required_roles, str):
            required_roles = [required_roles]

        return bool(set(user_roles) & set(required_roles))
