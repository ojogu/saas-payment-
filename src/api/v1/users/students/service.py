import requests
from sqlalchemy import true
from datetime import datetime
from api.v1.users .model import Level, Session, PaymentItem, Payment, User, TransactionStatus, Organization
from api.v1.users.model import Department
from utils.util import get_env_value, generate_payment_ref_number
from utils.dependency import db
from api.v1.auth.service import AuthService
from utils.exception import InUseError, NotFoundError, AlreadyExistsError, NotActive, InvalidPaymentItem, PaymentNotFound
from .schema import payment_schema
import logging
import hmac
import hashlib

#setup logging
service_logger = logging.getLogger(__name__)
service_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('logs/payment.log')
file_handler.setFormatter(formatter)
service_logger.addHandler(file_handler)

class PaymentService:
    def __init__(self):
        self.db = db
        self.auth = AuthService(model=User)
        self.paystack_secret_key = get_env_value("PRIVATE_KEY")
    
    def has_paid_for_item(self,  user_id, payment_item_id):
        payment = db.session.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.payment_item_id == payment_item_id,
            Payment.status == 'Paid'
        ).first()
        return payment is not None


    def validate_user_eligibility(self, user_id, payment_item_id):
        payment_item = db.session.query(PaymentItem).filter_by(id=payment_item_id).first()
        if not payment_item:
            raise Exception("Invalid payment item.")
        # Additional eligibility checks can go here.
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            raise Exception("User not found.")

    def initialize_payment(self, user_email, amount, reference):
        payload = {
            "email": user_email,
            "amount": int(amount * 100),  # Convert to kobo
            "reference": reference,
            "callback_url": "https://nwsst1n3-3002.uks1.devtunnels.ms/student"
        }
        headers = {
            "Authorization": f"Bearer {self.paystack_secret_key}",
            "Content-Type": "application/json"
        }
        response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
        service_logger.info(f"Payment initialized: {response.json()}") 
        return response.json()

    def create_payment(self, user_id, payment_item_id, amount, reference, url):
        payment = Payment(
            user_id=user_id,
            payment_item_id=payment_item_id,
            payment_method="Paystack",
            amount=amount,
            status="Pending",
            payment_reference=reference,
            url = url,
            payment_date=datetime.now()
        )
        self.db.session.add(payment)
        self.db.session.commit()
        service_logger.info(f"Payment created: {payment}")
        return payment
    
    def verify_payment(self, payment_reference):
            """Verify payment with Paystack"""
            headers = {
                "Authorization": f"Bearer {self.paystack_secret_key}"
            }
            response = requests.get(
                f"https://api.paystack.co/transaction/verify/{payment_reference}",
                headers=headers
            )
            service_logger.info(f"Payment verified: {response.json()}")
            return response.json()

    def verify_webhook_signature(self, signature, payload):
        """Verify that webhook is from Paystack"""
        computed_hmac = hmac.new(
            self.paystack_secret_key.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(computed_hmac, signature)


    def update_payment_status(self, reference, transaction_id, status):
        """Update payment status after verification"""
        # Fetch the payment record
        payment = self.db.session.query(Payment).filter_by(
            payment_reference=reference
        ).first()
        service_logger.info(f"Payment found: {payment}")
        
        if payment:
            # Construct the result dictionary
            result = {
                'user_id': payment.user_id,
                'id': payment.id,
                'payment_reference': payment.payment_reference,
                'transaction_id': transaction_id,
                'payment_item': payment.payment_item.name,
                'status': TransactionStatus.PAID.value,
                'amount': payment.amount,
                'payment_method': payment.payment_method,
                'date': payment.payment_date,
                'updated_at': payment.updated_at,
            }

            # Update the fields of the payment object from the result dictionary
            payment.transaction_id = result['transaction_id']
            payment.status = result['status']
            payment.updated_at = result['updated_at']

            # Commit the changes to the database
            self.db.session.commit()

            # Log and return the updated result
            service_logger.info(f"Payment updated: {result}")
            return result

        # Log and return None if no payment was found
        service_logger.warning("Payment not found for the given reference.")
        return None

    def get_updated_payment_status(self, reference):
        """Get updated payment status"""
        payment = self.db.session.query(Payment).filter_by(
            payment_reference=reference
        ).first()
        result = {
            'id': payment.id,
            'paymentreference': payment.payment_reference,
            'transaction_id': payment.transaction_id,
            'status': payment.status,
            'amount': payment.amount,
            'payment_method': payment.payment_method,
            'date': payment.date,
            'updated_at': payment.updated_at,
        }
        return result

class StudentService:
    def __init__(self):
        self.user = User
        self.db = db
        self.auth = AuthService(model=self.user)
        self.payment = PaymentService()

    def fetch_all_payment_items_by_session(self):
        """Fetch all payment items with their status for the current user based on academic session"""
        service_logger.info(f"Starting fetch all payment items by session process")
        student = self.auth.get_current_user()

        # Query for active session
        active_session = (
        db.session.query(Session.name)
        .join(Organization, Session.organization_id == Organization.id)
        .filter(Organization.acronym == student.organization.acronym, Session.is_active == True)
        .scalar())
        if not active_session:
            raise NotActive("No active session found for the student's organization")

        # Prepare filters for PaymentItem query
        organization_acronym = student.organization.acronym
        department_name = student.department.name
        level_name = student.level.name

        # Query for PaymentItem with payment status
        query = (
            db.session.query(PaymentItem, Payment.status)
            .join(Department, PaymentItem.department_id == Department.id)
            .join(Level, PaymentItem.level_id == Level.id)
            .join(Organization, Department.organization_id == Organization.id)
            .join(Session, PaymentItem.academic_session_id == Session.id)
            .outerjoin(Payment, db.and_(
                Payment.payment_item_id == PaymentItem.id,
                Payment.user_id == student.id
            ))
            .filter(
                Session.name == active_session,  # Use exact match for better performance
                Organization.acronym == organization_acronym,
                Department.name == department_name,
                Level.name == level_name,
            )
        )

        result = [
            {
                'id': item.id,
                'name': item.name,
                'amount': item.amount,
                'academic_session': item.academic_session.name,
                'level': item.level.name,
                'department': item.department.name,
                'organization': item.organization.name,
                'status': status if status else 'Not Paid'
            } for item, status in query.all()
        ]
        service_logger.info(f"Fetched payment items with status: {result}")
        return result
    
    def process_payment(self, payment_item_id, amount):
        user_id = self.auth.get_current_user().id
        user_email = self.auth.get_current_user().email
            
        if self.payment.has_paid_for_item(user_id, payment_item_id):
                raise AlreadyExistsError("User has already paid for this item.")
            
        self.payment.validate_user_eligibility(user_id, payment_item_id)
            
        payment_item = self.db.session.query(PaymentItem).filter_by(id=payment_item_id).first()
        if not payment_item:
                raise InvalidPaymentItem("Invalid payment item.")
            
        payment_item_amount = float(payment_item.amount)
        if payment_item_amount != amount:
            service_logger.info(f"amount: {type(amount)}")
            service_logger.info(f"payment_item.amount: {type(payment_item_amount)}")
            raise ValueError("Invalid amount for payment items.")
                
        reference = generate_payment_ref_number("PAY")
            
        response = self.payment.initialize_payment(
                user_email=user_email,
                amount=payment_item.amount,
                reference=reference
            )
            
        if not response.get('status'):
                raise NotActive("Failed to initialize payment with Paystack")
                
        payment = self.payment.create_payment(
                user_id=user_id,
                payment_item_id=payment_item_id,
                amount=payment_item.amount,
                reference=reference, 
                url=response['data']['authorization_url']
            )
        
        payment_dump = payment_schema.dump(payment)
        service_logger.info(f"Returning payment: {payment_dump}")
        service_logger.info(f"Returning authorization_url: {response['data']['authorization_url']}")
        service_logger.info(f"Returning amount: {str(payment_item.amount)}")
        
        return {
                "payment": payment_dump,
                "reference": response['data']['reference'],
                "authorization_url": response['data']['authorization_url'],
            }

    def fetch_all_paid_items(self):
        user = self.auth.get_current_user()
        service_logger.info(f"Fetching all paid items for user: {user.id}")

        active_session = (
            self.db.session.query(Session.id)
            .join(Organization, Session.organization_id == Organization.id)
            .filter(Organization.acronym == user.organization.acronym, Session.is_active == True)
            .scalar()
        )

        if not active_session:
            raise NotActive("No active session found for the user's organization")

        query = (
            self.db.session.query(Payment)
            .join(PaymentItem)
            .join(Department, PaymentItem.department_id == Department.id)
            .join(Level, PaymentItem.level_id == Level.id)
            .filter(
                Payment.user_id == user.id,
                Payment.status == 'Paid',
                PaymentItem.academic_session_id == active_session,
                Department.name == user.department.name,
                Level.name == user.level.name,
                Organization.acronym == user.organization.acronym
            )
        )

        result = [
            {
                'id': payment.id,
                'item_name': payment.payment_item.name,
                # 'payment_item': payment.payment_item.name,
                'amount': payment.amount,
                'date_paid': payment.payment_date.strftime("%Y-%m-%d"),
                'status': payment.status,
                'reference': payment.payment_reference
            } for payment in query.all()
        ]
        service_logger.info(f"Fetched paid items: {result}")
        return result
    
    def fetch_all_items_not_paid(self):        
        user = self.auth.get_current_user()
        user_id = user.id
        organization_acronym = user.organization.acronym
        level_name = user.level.name        
        department_name = user.department.name
        organization_acronym = user.organization.acronym
        """Fetch active session name for a particular user organization"""
        active_session = (
            db.session.query(Session.name)
            .join(Organization, Session.organization_id == Organization.id)
            .filter(
                Organization.acronym == organization_acronym,
                Session.is_active == True
            )
            .scalar()
        )
        session_name = active_session
        service_logger.info(f"Fetching pending payments for user: name- {user.first_name}, id -{user.id}")
        active_session = (
            db.session.query(Session.id)
            .join(Organization, Session.organization_id == Organization.id)
            .filter(
                Organization.acronym == organization_acronym,
                Session.name.ilike(f"%{session_name}%"),
                Session.is_active == True
            )
            .scalar()
        )

        if not active_session:
            print("No active session found.")
            return []

        query = (
            db.session.query(PaymentItem)
            .join(Department, PaymentItem.department_id == Department.id)
            .join(Level, PaymentItem.level_id == Level.id)
            .join(Organization, Department.organization_id == Organization.id)
            .join(Session, PaymentItem.academic_session_id == Session.id)
            .filter(
                Session.name == active_session,  # Use exact match for better performance
                Organization.acronym == organization_acronym,
                Department.name.ilike(f"%{department_name}%"),
                Level.name.ilike(f"%{level_name}%"),
                ~PaymentItem.id.in_(
                    db.session.query(Payment.payment_item_id).filter(Payment.user_id == user_id)
                )
            )
        )
        result = [
            {
                'id': item.id,
                'name': item.name,
                'amount': item.amount,
                'academic_session': item.academic_session.name,
                'level': item.level.name,
                'department': item.department.name,
                'organization': item.organization.name,
            } for item in query.all()
        ]
        service_logger.info(f"Fetched items not paid: {result}")
        return result

    def fetch_payment(self, payment_id):
        payment = self.db.session.query(Payment).filter_by(id=payment_id).first()
        if not payment:
            raise PaymentNotFound("Payment not found.")
        return payment
    
    def fetch_pending_payments(self):
        user = self.auth.get_current_user()
        user_id = user.id
        organization_acronym = user.organization.acronym
        level_name = user.level.name        
        department_name = user.department.name
        organization_acronym = user.organization.acronym
        """Fetch active session name for a particular user organization"""
        active_session = (
            db.session.query(Session.id)
            .join(Organization, Session.organization_id == Organization.id)
            .filter(
                Organization.acronym == organization_acronym,
                Session.is_active == True
            )
            .scalar()
        )
        session_name = active_session
        service_logger.info(f"Fetching pending payments for user: name- {user.first_name}, id -{user.id}")
        if not active_session:
            print("No active session found.")
            return []

        query = (
            db.session.query(Payment)
            .join(User)
            .join(PaymentItem)
            .join(Department, PaymentItem.department_id == Department.id)
            .join(Level, PaymentItem.level_id == Level.id)
            .join(Organization, Department.organization_id == Organization.id)
            .filter(
                Organization.acronym == organization_acronym,
                Department.name.ilike(f"%{department_name}%"),
                Level.name.ilike(f"%{level_name}%"),
                PaymentItem.academic_session_id == active_session,
                User.id == user_id,
                Payment.status == TransactionStatus.PENDING.value
            )
            .add_columns(User.email)
        )
        result =  query.all()
        if not result:
            service_logger.info("No pending payments found for the current user.")
            return []

        result = [
            {
                'id': payment.id,
                'item_name': payment.payment_item.name,
                'amount': payment.amount,
                'date_paid': payment.payment_date.strftime("%Y-%m-%d"),
                'status': payment.status,
                'reference': payment.payment_reference
            } for payment, _ in result
        ]
        service_logger.info(f"Fetched pending payments: {result}")
        return result




