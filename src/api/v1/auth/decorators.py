from functools import wraps
from api.v1.super_admin.model import SuperAdmin
from api.v1.users.model import User
from api.v1.auth.service import AuthService, auth_logger
from typing import Any, List, Union
from utils.exception import NotFoundError, AlreadyExistsError, InvalidEmailPassword
from enum import Enum

# Import your RoleEnum - adjust the import path as needed
from api.v1.users.model import RoleEnum


def check_role_permission(roles: Union[List[Union[str, RoleEnum]], None] = None):
    def decorator_func(f):
        @wraps(f)
        def decorator(*args: Any, **kwargs: Any) -> tuple:
            """
            Decorator to check if the current user has any of the specified roles.
            Works with both RoleEnum values and strings.
            """
            try:
                auth_logger.info("Checking role permission for user")
                
                # Convert all roles to their enum names for consistent comparison
                required_roles = []
                if roles:
                    for role in roles:
                        if isinstance(role, str):
                            try:
                                # Try to get enum member if string is provided
                                enum_role = RoleEnum[role]
                                required_roles.append(enum_role.name)
                            except KeyError:
                                # If not a valid enum name, use as is (for SUPERADMIN)
                                required_roles.append(role)
                        elif isinstance(role, RoleEnum):
                            required_roles.append(role.name)
                        else:
                            required_roles.append(str(role))

                auth_logger.info(f"Normalized required roles: {required_roles}")
                
                if not required_roles:
                    return f(*args, **kwargs)

                # Try SuperAdmin first if SUPERADMIN is in roles
                current_user = None
                if "SUPERADMIN" in required_roles:
                    try:
                        super_auth_service = AuthService(model=SuperAdmin)
                        current_user = super_auth_service.get_current_user()
                        if current_user and current_user.role == "SUPERADMIN":
                            auth_logger.info("Permission granted for superadmin")
                            return f(*args, **kwargs)
                    except NotFoundError:
                        pass

                # Check User model for all other roles
                user_auth_service = AuthService(model=User)
                try:
                    if not current_user:
                        current_user = user_auth_service.get_current_user()
                except NotFoundError:
                    auth_logger.warning("User not found")
                    return {"message": "Not found"}, 404

                if not current_user:
                    auth_logger.warning("No user found")
                    return {"message": "Not found"}, 404

                # Get the raw role string
                user_role = str(current_user.role)
                auth_logger.debug(f"Raw user role string: {user_role}")

                # Extract the actual role name
                if "RoleEnum." in user_role:
                    # Handle direct enum string format
                    user_role = user_role.split("RoleEnum.")[-1].strip("'()>")
                elif "<Role(name='" in user_role:
                    # Handle SQLAlchemy Role model format
                    user_role = user_role.split("<Role(name='")[-1].split("'")[0]
                    if "RoleEnum." in user_role:
                        user_role = user_role.split("RoleEnum.")[-1]
                
                # Clean up any remaining special characters
                user_role = user_role.strip("'()>").strip()
                
                auth_logger.info(f"Parsed user role: {user_role}")
                auth_logger.debug(f"Comparing against required roles: {required_roles}")

                # Check if user has any of the specified roles
                if user_role in required_roles:
                    auth_logger.info(f"Permission granted for role: {user_role}")
                    return f(*args, **kwargs)

                auth_logger.warning(f"Permission denied. User role '{user_role}' not in required roles: {required_roles}")
                return {"message": "Permission denied"}, 403

            except KeyError as e:
                auth_logger.error(f"Unexpected error while checking permissions: {str(e)}")
                return {"message": "Internal server error"}, 500

        return decorator
    return decorator_func