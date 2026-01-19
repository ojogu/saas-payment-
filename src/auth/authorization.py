from typing import List
from src.base.exception import AuthorizationError
from src.service.user_service import UserService
from src.utils.log import setup_logger

logger = setup_logger(__name__, "authorization.log")


class RoleCheck:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def check(self, required_roles: List[str]):
        current_user = self.user_service.get_current_user()
        logger.info(f"Role check for user {current_user['id']} with role {current_user['role']} against required roles {required_roles}")

        user_role = current_user['role']

        access = self.has_access(required_roles, [user_role])
        if not access:
            logger.warning(f"Access denied for user {current_user['id']}: required roles {required_roles}, user role {user_role}")
            raise AuthorizationError(f"Access denied. Required roles: {required_roles}")

    def has_access(self, required_roles: List[str], user_roles: List[str]) -> bool:
        # Ensure single string role is treated as a list
        if isinstance(user_roles, str):
            user_roles = [user_roles]

        if isinstance(required_roles, str):
            required_roles = [required_roles]

        return bool(set(user_roles) & set(required_roles))
