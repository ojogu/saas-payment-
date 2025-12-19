from typing import Any, Optional
from flask import jsonify
from src.base.schema import SuccessResponse, ErrorResponse


def success_response(status_code: int, message: str="success", data: Optional[Any] = None):
    '''Returns a JSON response for success responses'''
    response_content = SuccessResponse(message=message, data=data)
    return jsonify(response_content.model_dump), status_code

def error_response(status_code: int, message: str, error_code: Optional[str] = None, resolution: Optional[str] = None, data: Optional[Any] = None):
    '''Returns a JSON response for error responses'''
    response_content = ErrorResponse(message=message, error_code=error_code, resolution=resolution, data=data)
    return jsonify(response_content.model_dump()), status_code