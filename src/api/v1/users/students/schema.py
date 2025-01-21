from api.base.schema import BaseSchema
from marshmallow import fields

class StudentSchema(BaseSchema):
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    email = fields.Email()
    matric_number = fields.String(required=True) 
    faculty = fields.String(required=True) 
    campus = fields.String(required=True) 
    residential_address = fields.String(required=True)
    department = fields.String()
    organization = fields.String()
    phone = fields.String(required=True)
    level = fields.String(required=True)


student_schema = StudentSchema()
students_schema = StudentSchema(many=True)
student_schema_dump = StudentSchema(exclude=["created_at", "updated_at"])

class Payment( BaseSchema):
    payment_item_id = fields.Integer()
    amount = fields.Float()

payment = Payment(exclude=["created_at", "updated_at"])


class PaymentSchema(BaseSchema):
        id = fields.Integer()
        reference = fields.String()
        item_name = fields.String()
        transaction_id = fields.String()
        status = fields.String()
        amount = fields.String()
        reference = fields.String()
        payment_method = fields.String()
        date = fields.DateTime()



payment_schema = PaymentSchema(exclude=["created_at", "updated_at"])
payments_schema = PaymentSchema(many=True)


class PaymentResponseSchema(BaseSchema):
    payment = fields.Nested(PaymentSchema)
    authorization_url = fields.String()
    reference = fields.String()
payment_response_schema = PaymentResponseSchema(only=["payment", "authorization_url", "reference"])




class StudentInfoSchema(BaseSchema):
    name = fields.String()
    organization = fields.String()
    matric_number = fields.String()
    department = fields.String()
    level = fields.String()
    faculty = fields.String()
    campus = fields.String()


class PaymentInfoSchema(BaseSchema):
    name = fields.String()
    amount = fields.Float()
    status = fields.String()
    reference = fields.String()
    transaction_id = fields.String()
    payment_method = fields.String()
    session = fields.String()
    date = fields.String()


class ReceiptSchema(BaseSchema):
    receipt_no = fields.String()
    date = fields.String()
    student_info = fields.Nested(StudentInfoSchema)
    payment_info = fields.Nested(PaymentInfoSchema)
    
    
receipt_schema = ReceiptSchema()


class SessionReceiptSchema(BaseSchema):
    receipt_no = fields.String()
    date = fields.String()
    student_info = fields.Nested(StudentInfoSchema)
    session = fields.String()
    items = fields.Nested(PaymentInfoSchema, many=True)
    total_amount = fields.Float()


session_receipt_schema = SessionReceiptSchema()
