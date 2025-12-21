from datetime import timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required
import jwt
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from src.auth.schema import Login
from src.service.user_service import UserService
from src.utils.db import db
from src.utils.config import config
from src.utils.response import success_response
from src.schema.user import UpdatePassword

auth_bp = Blueprint("auth", __name__)



@auth_bp.route("/login", methods=["POST"])
def login():
    data:dict = request.get_json()
    validated_data = Login(**data)
    # credential = data.get("credential")
    # password = data.get("password")
     
    user_service = UserService(db)
    
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
    

@auth_bp.route("/update/password", methods=["POST"])
@jwt_required()
#add role decorator
def update_password():
    user_service = UserService(db)
    user = user_service.get_current_user()
    data:dict = request.get_json()
    
    #add user id
    data["user_id"] = user.id
    
    validated_data = UpdatePassword(**data)
    updated_password = user_service.update_password(validated_data)
    return success_response(
        message="successfully updated password"
    )
 
