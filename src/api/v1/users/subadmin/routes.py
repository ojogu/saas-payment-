# the routes for the admin services. onboards sub admin etc
from flask import Blueprint, request
from flask_restful import Resource, Api
from .service import StudentManagement, PaymentItemManagment
from .schema import payment_item_dump_schema, payment_items_schema
from api.v1.users.students.schema import student_schema_dump
from utils.response import custom_response
from utils.config import get_file_path
from sqlalchemy.exc import SQLAlchemyError
from utils.exception import InUseError, NotFoundError,AlreadyExistsError
from flask_jwt_extended import jwt_required
from api.v1.auth.decorators import check_role_permission
import logging
from werkzeug.utils import secure_filename

subadmin_blueprint = Blueprint("sub_admin", __name__, url_prefix="/api/admin/")
admin_api = Api(subadmin_blueprint)

# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("logs/error.log")

# Set level for handlers
console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.ERROR)

# Create formatters and add them to handlers
console_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_format)
file_handler.setFormatter(file_format)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class StudentResource(Resource):
    """
    Handles requests related to students.

    Attributes:
        service (StudentManagement): The service used to interact with the database.
        custom_response (custom_response): A custom response object used to generate responses.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = StudentManagement()
        self.custom_response = custom_response

    @jwt_required()
    @check_role_permission(["ADMIN"])
    def post(self) -> tuple:
        """
        Creates a new student.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            student = self.service.create(request.get_json())
            return self.custom_response.success_response(
                message="Student successfully created",
                data=student_schema_dump.dump(student),
                status_code=201
            )
        except InUseError as e:
            logger.warning(str(e))
            return self.custom_response.email_in_use_error(message="already exists")
        except AlreadyExistsError as e:
            logger.warning(str(e))
            return self.custom_response.bad_request_error(message="already exists")
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()

class Bulkupload(Resource):
    def __init__(self):
        self.service = StudentManagement()
        self.custom_response = custom_response
        
    method_decorators = [check_role_permission(["ADMIN"]), jwt_required()]
    def post(self):
        logger.info("Initiating file upload process")
        # Check if the file is part of the request
        if 'file' not in request.files:
            logger.warning("No file uploaded in the request")
            return self.custom_response.bad_request_error(message="No file uploaded")
        
        file = request.files['file']
        if file.filename == '':
            logger.warning("No file selected in the request")
            return self.custom_response.bad_request_error(message="No file selected")

        # Check if the file is an excel file
        if not file.filename.endswith('.xlsx') and not file.filename.endswith('.xls'):
            logger.warning("Invalid file extension uploaded")
            return self.custom_response.bad_request_error(message="Invalid file extension")

        # Save the file temporarily
        filename = secure_filename(file.filename)
        file_path = get_file_path(filename)
        file.save(file_path)
        logger.info(f"File saved temporarily at {file_path}")

        try:
            logger.info("Starting bulk student creation from uploaded file")
            data = self.service.bulk_creation(file_path)
            logger.info("Bulk student creation successful")
            return self.custom_response.success_response(
                message="File uploaded and processed successfully",
                data=student_schema_dump.dump(data, many=True),
                status_code=201
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error during bulk creation: {str(e)}")
            return self.custom_response.server_error()

        
class GetAllStudents(Resource):
    """
    Handles requests to fetch all students.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = StudentManagement()
        self.custom_response = custom_response

    method_decorators = [check_role_permission(["ADMIN", "SUBADMIN"]), jwt_required()]
    def get(self, filters: dict = None) -> tuple:
        """
        Fetches all students.

        Args:
            filters (dict): A dictionary containing filters to apply to the query.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            if filters is None:
                filters = request.args.to_dict()
            students = self.service.fetch_all(**filters)
            return self.custom_response.success_response(
                message="All students fetched successfully",
                data=student_schema_dump.dump(students, many=True),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()


class RetrieveUpdateDeleteStudent(Resource):
    """
    Handles requests to retrieve, update, and delete students.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = StudentManagement()
        self.custom_response = custom_response

    @jwt_required()
    @check_role_permission(["ADMIN", "SUBADMIN"])
    def get(self, matric_number: str = None) -> tuple:
        """
        Retrieves a specific student.

        Args:
            email (str): The email of the student to retrieve.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            student = self.service.fetch_one(matric_number=matric_number)
            return self.custom_response.success_response(
                message="Student fetched successfully",
                data=student_schema_dump.dump(student),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found error: {str(e)}")
            return self.custom_response.not_found_error()

    @jwt_required()
    @check_role_permission(["ADMIN"])
    def put(self, matric_number: str) -> tuple:
        """
        Updates a specific student.

        Args:
            email (str): The email of the student to update.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            student = self.service.update(matric_number, request.get_json())
            return self.custom_response.success_response(
                message="Student updated successfully",
                data=student_schema_dump.dump(student),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found: {str(e)}")
            return self.custom_response.not_found_error(message=f"{matric_number} not found")

    @jwt_required()
    @check_role_permission(["ADMIN"])
    def delete(self, matric_number: str) -> tuple:
        """
        Deletes a specific student.

        Args:
            email (str): The email of the student to delete.

        Returns:
            A tuple containing a message and a status code.
        """
        try:
            self.service.delete(matric_number)
            return self.custom_response.success_response(
                message="Student deleted successfully",
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found: {str(e)}")
            return self.custom_response.not_found_error(message=f"{matric_number} not found")
        except ValueError as e:
            logger.error(f" {str(e)}")
            return self.custom_response.bad_request_error(message="email must be passed")

# student routes
admin_api.add_resource(StudentResource, "/student/create")
admin_api.add_resource(GetAllStudents, "/student/all")
admin_api.add_resource(RetrieveUpdateDeleteStudent, "student/<string:matric_number>")
admin_api.add_resource(Bulkupload, "student/bulk-create")


class PaymentResource(Resource):
    """
    Handles requests to create a payment.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = PaymentItemManagment()
        self.custom_response = custom_response

    @jwt_required()
    @check_role_permission(["ADMIN", "SUBADMIN"])
    def post(self) -> tuple:
        
        try:
            payment = self.service.create(request.get_json())
            return self.custom_response.success_response(
                message="Payment created successfully",
                data=payment_item_dump_schema.dump(payment),
                status_code=201
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except InUseError as e:
            logger.error(f"In use error: {str(e)}")
            return self.custom_response.email_in_use_error(message="Cannot register payment item for an inactive session")

class Get_All_Payments(Resource):
    """
    Handles requests to get all payments.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = PaymentItemManagment()
        self.custom_response = custom_response

    @jwt_required()
    @check_role_permission(["ADMIN", "SUBADMIN"])
    def get(self) -> tuple:
        try:
            payments = self.service.fetch_all()
            logger.info(f"Payments: {payments}")
            return self.custom_response.success_response(
                message="Payments fetched successfully",
                data=payment_items_schema.dump(payments),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found error: {str(e)}")
            return self.custom_response.not_found_error()

class RetrieveUpdateDeletePayment(Resource):
    """
    Handles requests to retrieve, update, and delete payments.
    """

    def __init__(self):
        """
        Initializes the resource with a service and a custom response object.
        """
        self.service = PaymentItemManagment()
        self.custom_response = custom_response

    @jwt_required()
    @check_role_permission(["ADMIN", "SUBADMIN"])
    def get(self) -> tuple:
        """
        Retrieves a specific payment.

        Args:
            name (str): The name of the payment to retrieve.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            name = request.args.get("name")
            level = request.args.get("level")
            department = request.args.get("department")
            payment = self.service.fetch_one(name=name, level=level, department_name=department)
            return self.custom_response.success_response(
                message="Payment fetched successfully",
                data=payment_item_dump_schema.dump(payment),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found error: {str(e)}")
            return self.custom_response.not_found_error()
    
    @jwt_required()
    @check_role_permission(["ADMIN", "SUBADMIN"])
    def put(self) -> tuple:
        """
        Updates a specific payment.

        Args:
            name (str): The name of the payment to update.

        Returns:
            A tuple containing a message, data, and a status code.
        """
        try:
            name = request.args.get("name")
            level = request.args.get("level")
            payment = self.service.update(name=name, level=level, request_data=request.get_json())
            return self.custom_response.success_response(
                message="Payment updated successfully",
                data=payment_item_dump_schema.dump(payment),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        
        except NotFoundError as e:
            logger.error(f"Not found error: {str(e)}")
            return self.custom_response.not_found_error()
    
    @jwt_required()
    @check_role_permission(["ADMIN", "SUBADMIN"])
    def delete(self) -> tuple:
        """
        Deletes a specific payment.

        Args:
            name (str): The name of the payment to delete.

        Returns:
            A tuple containing a message and a status code.
        """
        try:
            name = request.args.get("name")
            level = request.args.get("level")
            department = request.args.get("department")
            self.service.delete(name=name, level=level, department_name=department)
            return self.custom_response.success_response(
                message="Payment deleted successfully",
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found error: {str(e)}")
            return self.custom_response.not_found_error()
        
#payment routes
admin_api.add_resource(PaymentResource, "/payment/create")
admin_api.add_resource(Get_All_Payments, "/payment/all")
admin_api.add_resource(RetrieveUpdateDeletePayment, "payment/")