from flask import Blueprint, request
from flask_restful import Resource, Api
import logging
from .service import StudentService, PaymentService
from utils.exception import InUseError, NotFoundError, AlreadyExistsError, NotActive, InvalidPaymentItem, PaymentNotFound
from utils.response import custom_response
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required
from api.v1.auth.decorators import check_role_permission
from .schema import payment, payment_schema, payment_response_schema, payments_schema, receipt_schema, session_receipt_schema
from api.v1.reciepts.service import receipt_service
import json 
from api.v1.users.subadmin.schema import payment_item_dump_schema
student_blueprint = Blueprint("student", __name__, url_prefix="/api/student/")

student_api = Api(student_blueprint)

# Create a custom logger
#setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/payment.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Student(Resource):
    def __init__(self):
        self.custom_response = custom_response
        self.service = StudentService()

    @jwt_required()
    @check_role_permission(["STUDENT"])
    def get(self):
        #get all payment items based on his organization, department, level and session
        logger.info("Fetching payment items")
        try:
            payment_items = self.service.fetch_all_payment_items_by_session()
            return self.custom_response.success_response(
                message="Payment items fetched successfully",
                data=payment_item_dump_schema.dump(payment_items, many=True),
                status_code=200
        )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found error: {str(e)}")
            return self.custom_response.not_found_error(message="payment items not found")
        except NotActive as e:
            logger.error(f"Not active error: {str(e)}")
            return self.custom_response.not_found_error(message="No active session found")


class Get_All_Items_Not_Paid(Resource):
    def __init__(self):
        self.service = StudentService()
        self.custom_response = custom_response

    @jwt_required()
    @check_role_permission(["STUDENT"])
    def get(self):
        try:
            payment_items = self.service.fetch_all_items_not_paid()
            return self.custom_response.success_response(
                message="Payment items fetched successfully",
                data=payments_schema.dump(payment_items, many=True),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found error: {str(e)}")
            return self.custom_response.not_found_error(message="payment items not found")
        except NotActive as e:
            logger.error(f"Not active error: {str(e)}")
            return self.custom_response.not_found_error(message="No active session found")




class Get_All_Paid_Items(Resource):
    def __init__(self):
        self.service = StudentService()
        self.custom_response = custom_response

    @jwt_required()
    @check_role_permission(["STUDENT"])
    def get(self):    
        try:
            payment_items = self.service.fetch_all_paid_items()
            return self.custom_response.success_response(
                message="Payment items fetched successfully",
                data=payments_schema.dump(payment_items, many=True),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found error: {str(e)}")
            return self.custom_response.not_found_error(message="payment items not found")
        except NotActive as e:
            logger.error(f"Not active error: {str(e)}")
            return self.custom_response.not_found_error(
                message="No active session found"
            )

class Get_All_Pending_Items(Resource):
    def __init__(self):
        self.service = StudentService()
        self.custom_response = custom_response

    @jwt_required()
    @check_role_permission(["STUDENT"])
    def get(self):
        try:
            payment_items = self.service.fetch_pending_payments()
            return self.custom_response.success_response(
                message="Pending Payment items fetched successfully",
                data=payments_schema.dump(payment_items, many=True),
                status_code=200
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return self.custom_response.server_error()
        except NotFoundError as e:
            logger.error(f"Not found error: {str(e)}")
            return self.custom_response.not_found_error(message="payment items not found")
        except PaymentNotFound as e:
            logger.error(f"Payment not found error: {str(e)}")
            return self.custom_response.not_found_error(message="Payment not found")
        except NotActive as e:
            logger.error(f"Not active error: {str(e)}")
            return self.custom_response.not_found_error(
                message="No active session found"
            )


class ProcessPaymentResource(Resource):
    def __init__(self):
        self.service = StudentService()
        self.custom_response = custom_response
        
    @jwt_required()
    @check_role_permission(["STUDENT"])
    def post(self):
        try:
            errors = payment.validate(request.get_json())
            if errors:
                return {'message': 'Validation errors', 'errors': errors}, 400

            data = payment.load(request.get_json())
            payment_item_id = data['payment_item_id']
            amount = data['amount']

            result = self.service.process_payment(payment_item_id, amount)
            logger.info(f"Payment result: {result}")
            return self.custom_response.success_response(
                message="Payment created successfully",
                data=payment_response_schema.dump(result))
            
        except AlreadyExistsError as e:
            logger.error(f"Already exists error: {str(e)}")
            return self.custom_response.bad_request_error(message=str(e))
        except InvalidPaymentItem as e:
            logger.error(f"Invalid request error: {str(e)}")
            return self.custom_response.bad_request_error(message=str(e))
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return self.custom_response.bad_request_error(message=str(e))


class VerifyPaymentResource(Resource):
    def __init__(self):
        self.service = PaymentService()
        self.custom_response = custom_response
    
    @jwt_required()
    @check_role_permission(["STUDENT"])
    def get(self, reference):
        try:
            logger.info(f"Verifying payment for reference: {reference}")
            verfication = self.service.verify_payment(reference)
            logger.info(f"Payment verification result: {verfication}")
            if verfication['status'] and verfication['data']['status'] == 'success':
                payment = self.service.update_payment_status(
                    reference=reference,
                    transaction_id=verfication['data']['id'],
                    status="Paid"
                )
                return self.custom_response.success_response(
                    message="Payment verification successful",
                    data={'payment': payment_schema.dump(payment)}
                )
            return self.custom_response.bad_request_error(
                message="Payment verification failed"
            )
        except NotFoundError as e:
            logger.error(f"Not found error: {str(e)}")
            return self.custom_response.not_found_error(message="Payment not found")
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return self.custom_response.bad_request_error(message=str(e))
        
class PaystackWebhookResource(Resource):
    def __init__(self):
        self.service = PaymentService()
        self.custom_response = custom_response
        self.reciept = receipt_service
    def post(self):
        try:
            signature = request.headers.get("x-paystack-signature")
            if not signature:
                return self.custom_response.bad_request_error(
                    message='Missing signature'
                )

            payload = request.get_data()
            
            if not self.service.verify_webhook_signature(signature, payload):
                return self.custom_response.error_response(
                    message='Invalid signature',
                    error_code=400
                )
            
            payload_data = json.loads(payload)
            
            if payload_data.get('event') == 'charge.success':
                data = payload_data['data']
                payment_reference = data['reference']
                transaction_id = data['id']
                
                verification = self.service.verify_payment(payment_reference)
                
                if verification['status'] and verification['data']['status'] == 'success':
                    payment = self.service.update_payment_status(
                        payment_reference=payment_reference,
                        transaction_id=transaction_id,
                        status="Paid"
                    )
                    
                    if payment:
                        pass
                        id = payment.get('id')
                        reciept = self.reciept.generate_item_receipt(id)
                        # Trigger additional actions (email, invoice, etc.)
            
            return self.custom_response.success_response(
                message="Webhook processed successfully", 
                status_code=200
            )

        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return self.custom_response.error_response(
                message="Internal server error",
                status_code=500
            )

class PaymentReceiptResource(Resource):
    def __init__(self):
        self.service = PaymentService()
        self.custom_response = custom_response
        self.receipt = receipt_service
    
    @jwt_required()
    @check_role_permission(["STUDENT"])
    def get(self, payment_reference):
        receipt = receipt_service.generate_item_receipt(payment_reference)
        return self.custom_response.success_response(
            message="Receipt generated successfully",
            data=receipt_schema.dump(receipt)
        )

class SessionReciept(Resource):
    def __init__(self):
        self.service = PaymentService()
        self.custom_response = custom_response
        self.receipt = receipt_service

    @jwt_required()
    @check_role_permission(["STUDENT"])
    def get(self):
        logger.info("entry")
        receipt = receipt_service.generate_session_receipt()
        logger.info(receipt)
        return self.custom_response.success_response(
            message="Receipt generated successfully",
            data=session_receipt_schema.dump(receipt)
        )
#routes
#fetch all payment items
student_api.add_resource(Student, "/payment-items")
#fetch all items not paid
student_api.add_resource(Get_All_Items_Not_Paid, "/payment-items/not-paid")
#fetch all items paid
student_api.add_resource(Get_All_Paid_Items, "/payment-items/paid")
#fetch all items pending
student_api.add_resource(Get_All_Pending_Items, "/payment-items/pending")

###### payment routes ########
student_api.add_resource(ProcessPaymentResource, '/payments/process')
student_api.add_resource(VerifyPaymentResource, '/payments/verify/<string:reference>')
student_api.add_resource(PaystackWebhookResource, '/webhook/paystack')

### receipt routes
student_api.add_resource(PaymentReceiptResource, '/receipts/<string:payment_reference>')
student_api.add_resource(SessionReciept, '/receipts/session')