from datetime import timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity, get_jwt
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from dishka.integrations.flask import FromDishka, inject
from src.auth.schema import Login
from src.service.user_service import UserService
from src.utils.config import config
from src.utils.response import success_response
from src.schema.user import UpdatePassword

auth_bp = Blueprint("auth", __name__)



@auth_bp.route("/login", methods=["POST"])
@inject
def login(user_service: FromDishka[UserService]):
    data:dict = request.get_json()
    validated_data = Login(**data)
    # credential = data.get("credential")
    # password = data.get("password")
    
    user:dict = user_service.authenticate_user(validated_data)
    access_token = create_access_token(
        identity=user.get("user_id"),
        additional_claims=user.get("role"),
        expires_delta=timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRES)
        )
    
    refresh_token = create_refresh_token(
        identity=user.get("user_id"),
        additional_claims=user.get("role"),
        expires_delta=timedelta(days=config.JWT_REFRESH_TOKEN_EXPIRES)
        )
    
    data = {"access_token": access_token,
         "refresh_token": refresh_token,
         "token_type": "Bearer",
         "expires_in": config.JWT_ACCESS_TOKEN_EXPIRES,
         "user_data": {
             "user_id": user["user_id"],
             "role": user["role"]
         }
        }
    return success_response(
        message="Tokens Successfully Generated",
        status_code=200,
        data=data
    )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_refresh_token_required()
def refresh_access_token():
    """
    Refresh access token using a valid refresh token.
    """
    # Get the identity and claims from the refresh token
    user_id = get_jwt_identity()
    claims = get_jwt()

    # Create a new access token
    access_token = create_access_token(
        identity=user_id,
        additional_claims=claims,
        expires_delta=timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRES)
    )

    data = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": config.JWT_ACCESS_TOKEN_EXPIRES
    }

    return success_response(
        message="Access token refreshed successfully",
        status_code=200,
        data=data
    )


@auth_bp.route("/update/password", methods=["POST"])
@jwt_required()
@inject
#add role decorator
def update_password(user_service: FromDishka[UserService]):
    user = user_service.get_current_user()
    data:dict = request.get_json()
    
    #add user id
    data["user_id"] = user.id
    
    validated_data = UpdatePassword(**data)
    updated_password = user_service.update_password(validated_data)
    return success_response(
        message="successfully updated password"
    )
