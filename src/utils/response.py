from typing import Any, Optional
from flask import jsonify
from src.base.schema import SuccessResponse, ErrorResponse


def success_response(status_code: int, message: str="success", data: Optional[Any] = None):
    '''Returns a JSON response for success responses'''
    response_content = SuccessResponse(message=message, data=data)
    return jsonify(response_content.model_dump()), status_code

def error_response(status_code: int, message: str, error_code: Optional[str] = None, resolution: Optional[str] = None, data: Optional[Any] = None):
    '''Returns a JSON response for error responses'''
    response_content = ErrorResponse(message=message, error_code=error_code, resolution=resolution, data=data)
    return jsonify(response_content.model_dump()), status_code



# from http import HTTPStatus

# # Success
# HTTPStatus.OK                     # 200
# HTTPStatus.CREATED                # 201
# HTTPStatus.ACCEPTED               # 202
# HTTPStatus.NO_CONTENT             # 204

# # Redirection
# HTTPStatus.MOVED_PERMANENTLY      # 301
# HTTPStatus.FOUND                  # 302
# HTTPStatus.NOT_MODIFIED           # 304

# # Client Errors
# HTTPStatus.BAD_REQUEST            # 400
# HTTPStatus.UNAUTHORIZED           # 401
# HTTPStatus.FORBIDDEN              # 403
# HTTPStatus.NOT_FOUND              # 404
# HTTPStatus.METHOD_NOT_ALLOWED     # 405
# HTTPStatus.CONFLICT               # 409
# HTTPStatus.UNPROCESSABLE_ENTITY   # 422

# # Server Errors
# HTTPStatus.INTERNAL_SERVER_ERROR  # 500
# HTTPStatus.NOT_IMPLEMENTED        # 501
# HTTPStatus.BAD_GATEWAY            # 502
# HTTPStatus.SERVICE_UNAVAILABLE    # 503