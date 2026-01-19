from flask import jsonify, Flask
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from src.base.schema import ErrorResponse
from http import HTTPStatus
from src.base.exception import (
    BaseExceptionClass,
    Environment_Variable_Exception,
    InUseError,
    TokenExpired,
    InvalidToken,
    NotFoundError,
    AlreadyExistsError,
    InvalidEmailPassword,
    BadRequest,
    NotVerified,
    EmailVerificationError,
    DatabaseError,
    ServerError,
    NotActive, 
    AuthorizationError
)
from src.utils.log import setup_logger
exception_logger = setup_logger(__name__, file_path="error.log")


def create_exception_handler(status_code:int, initial_detail:dict):
    """Create a standardized exception handler for Flask"""
    #this handler handles only custom Exception class, the other uses direct decorator pattern
    def handler(exc:BaseExceptionClass): 
        # Log the exception details
        exception_logger.error(f"Exception occurred: {str(exc)}") 

        # Copy initial detail and override message if exception has one
        response_payload = initial_detail.copy()
        
        # Flask exceptions often use .description, custom ones might use .message
        if hasattr(exc, "message") and exc.message is not None:
            response_payload["message"] = str(exc.message)

        validated_data = ErrorResponse(**response_payload)
        return jsonify(validated_data.model_dump()), status_code
        

    return handler


#register handlers
def register_error_handlers(app:Flask):
    """Register all exception handlers for the Flask app"""
    
    # Custom exception handlers
    app.register_error_handler(
        Environment_Variable_Exception,
        create_exception_handler(
            status_code=500,
            initial_detail={
                "status": "error",
                "message": "Environment variable missing",
                "error_code": "environment_variable_missing",
                "data": None,
            }
        )
    )
    
    # Custom exception handlers
    app.register_error_handler(
        InUseError,
        create_exception_handler(
               status_code=409,
            initial_detail={
                "status": "error",
                "message": "Resource already in use",
                "error_code": "resource_in_use",
                "data": None,
                
            }
        )
    )
    
    

# --- Authorization & Tokens ---

    app.register_error_handler(
        AuthorizationError,
        create_exception_handler(
            status_code=HTTPStatus.FORBIDDEN,
            initial_detail={
                "status": "error",
                "message": "forbidden - user lacks required permissions",
                "error_code": "Forbidden_error",
                "data": None,
            }
        )
    )

    app.register_error_handler(
        InvalidToken,
        create_exception_handler(
            status_code=HTTPStatus.UNAUTHORIZED,
            initial_detail={
                "status": "error",
                "message": "access or refresh token invalid",
                "error_code": "Invalid_token",
                "data": None,
            }
        )
    )

    app.register_error_handler(
        TokenExpired,
        create_exception_handler(
            status_code=HTTPStatus.UNAUTHORIZED,
            initial_detail={
                "status": "error",
                "message": "Token expired",
                "error_code": "token_expired",
                "resolution": "Please get a new token",
                "data": None,
            }
        )
    )

    # --- Resource State & Existence ---

    app.register_error_handler(
        NotFoundError,
        create_exception_handler(
            status_code=HTTPStatus.NOT_FOUND,
            initial_detail={
                "status": "error",
                "message": "Resource not found",
                "error_code": "not_found",
                "data": None,
            }
        )
    )

    app.register_error_handler(
        AlreadyExistsError,
        create_exception_handler(
            status_code=HTTPStatus.CONFLICT,
            initial_detail={
                "status": "error",
                "message": "Resource already exists",
                "error_code": "already_exists",
                "data": None,
            }
        )
    )

    app.register_error_handler(
        InUseError,
        create_exception_handler(
            status_code=HTTPStatus.CONFLICT,
            initial_detail={
                "status": "error",
                "message": "Resource already in use",
                "error_code": "resource_in_use",
                "data": None,
            }
        )
    )

    # --- Authentication & Verification ---

    app.register_error_handler(
        InvalidEmailPassword,
        create_exception_handler(
            status_code=HTTPStatus.UNAUTHORIZED,
            initial_detail={
                "status": "error",
                "message": "Invalid email or password",
                "error_code": "invalid_credentials",
                "data": None,
            }
        )
    )

    app.register_error_handler(
        NotVerified,
        create_exception_handler(
            status_code=HTTPStatus.FORBIDDEN,
            initial_detail={
                "status": "error",
                "message": "Account not verified",
                "error_code": "not_verified",
                "resolution": "Please verify your account",
                "data": None,
            }
        )
    )

    app.register_error_handler(
        NotActive,
        create_exception_handler(
            status_code=HTTPStatus.FORBIDDEN,
            initial_detail={
                "status": "error",
                "message": "Account is not active",
                "error_code": "account_not_active",
                "resolution": "Please activate your account",
                "data": None,
            }
        )
    )

    # --- Requests & Validation ---

    app.register_error_handler(
        BadRequest,
        create_exception_handler(
            status_code=HTTPStatus.BAD_REQUEST,
            initial_detail={
                "status": "error",
                "message": "Bad request",
                "error_code": "bad_request",
                "data": None,
            }
        )
    )

    app.register_error_handler(
        EmailVerificationError,
        create_exception_handler(
            status_code=HTTPStatus.BAD_REQUEST,
            initial_detail={
                "status": "error",
                "message": "Email verification failed",
                "error_code": "email_verification_failed",
                "data": None,
            }
        )
    )

    # --- Server & Infrastructure ---

    app.register_error_handler(
        DatabaseError,
        create_exception_handler(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            initial_detail={
                "status": "error",
                "message": "Database error occurred",
                "error_code": "database_error",
                "data": None,
            }
        )
    )

    app.register_error_handler(
        ServerError,
        create_exception_handler(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            initial_detail={
                "status": "error",
                "message": "Internal server error",
                "error_code": "server_error",
                "data": None,
            }
        )
    )
    
    # catch standard HTTP errors this way
    app.register_error_handler(
        404,
        create_exception_handler(
            status_code=404,
            initial_detail={
                "status": "error",
                "message": "Resource not found",
                "error_code": "not_found",
                "data": None,
            }
        )
    )
    
    
    #specific Errors
    @app.errorhandler(ValidationError)
    def pydantic_validation_error_handler(exc: ValidationError):
        exception_logger.error(f"Pydantic validation error: {str(exc)}")
        
        # 1. Get the list of individual error dictionaries
        pydantic_errors = exc.errors()

        # 2. Extract the 'msg' (message) and optionally the 'loc' (location/field name) 
        #    from each error dictionary.
        formatted_messages = []
        for error in pydantic_errors:
            # 'loc' is a tuple/list indicating where the error occurred (e.g., ('body', 'level'))
            field_name = error['loc'][-1] if error['loc'] else 'Input'
            message = error['msg']
            
            # Format: "Field Name: Error Message"
            formatted_messages.append(f"Field '{field_name}': {message}")

        # 3. Join all formatted messages into a single string
        client_message = " | ".join(formatted_messages)
        content={
                "status": "error",
                "message": client_message,
                "error_code": "validation_error",
            
            }
        return jsonify(content), HTTPStatus.UNPROCESSABLE_ENTITY
    
    
    @app.errorhandler(SQLAlchemyError)
    def sqlalchemy_error_handler( exc: SQLAlchemyError):
        exception_logger.error(f"Database error: {str(exc)}")
        content={
                "status": "error",
                "message": "Database error",
                "error_code": "database_error",
                "data": None,
                
            },
        return jsonify(content), HTTPStatus.INTERNAL_SERVER_ERROR
    
    @app.errorhandler(IntegrityError)
    def integrity_error_handler( exc: IntegrityError):
        exception_logger.error(f"Database error: {str(exc)}")
        content={
                "status": "error",
                "message": "Database error",
                "error_code": "database_error",
                "data": None,
                
            },
        return jsonify(content), HTTPStatus.INTERNAL_SERVER_ERROR