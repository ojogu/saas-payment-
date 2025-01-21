from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Table, Text, ForeignKey, Integer, Enum, DECIMAL, CheckConstraint, Boolean, UniqueConstraint, Date, TIMESTAMP, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum as PyEnum
import datetime

class RoleEnum(PyEnum):
    ADMIN = "ADMIN"
    SUBADMIN = "SUBADMIN"
    BURSAR = "BURSAR"
    STUDENT = "STUDENT"

class TransactionStatus(PyEnum):
    PENDING = 'PENDING'
    SUCCESSFUL = 'SUCCESSFUL'
    FAILED = 'FAILED'
    PAID = "PAID"

class ClearanceStatus(PyEnum):
    PENDING = 'PENDING'
    ISSUED = 'ISSUED'
    NOTCLEARED = 'NOT_CLEARED'


# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = True

# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)

# Define the Department model

import sqlalchemy as sa
from uuid import uuid4
class BaseModel(db.Model):
    """
    Base model class for all models in the application.

    Contains common fields and methods used by all models.

    Fields:
        id: A unique identifier for the model.
        user_id: The UUID of the user who created the model.
        created_at: The timestamp when the model was created.
        updated_at: The timestamp when the model was last updated.
    """
    __abstract__ = True
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    entity_id = sa.Column(sa.UUID(as_uuid=True), nullable=False, default=uuid4, unique=True)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())

class Organization(BaseModel):
    __tablename__ = 'organizations'
    name = Column(String(255), nullable=False)
    acronym = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20))
    address = Column(Text)
    email = Column(String(255), nullable=False, unique=True)
    
    # Relationships with cascade
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="organization", cascade="all, delete-orphan")
    payment_items = relationship("PaymentItem", back_populates="organization", cascade="all, delete-orphan")
    clearance_items = relationship("Clearance", back_populates="organization", cascade="all, delete-orphan")

class User(BaseModel):
    __tablename__ = 'users'
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    matric_number = Column(String(50), unique=True, index=True)
    faculty = Column(String(100))
    campus = Column(String(100))
    residential_address = Column(Text)
    phone = Column(String(20), index=True)

    # Foreign keys
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete="SET NULL"))
    level_id = Column(Integer, ForeignKey('levels.id', ondelete="SET NULL"))

    # Relationships
    role = relationship("Role", back_populates="users")
    organization = relationship("Organization", back_populates="users")
    department = relationship("Department", back_populates="users")
    level = relationship("Level", back_populates="users")
    
    # One-to-Many relationships
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    clearances = relationship("Clearance", back_populates="user", cascade="all, delete-orphan")
    clearance_certificates_owned = relationship(
        "ClearanceCertificate",
        foreign_keys="ClearanceCertificate.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    clearance_certificates_issued = relationship(
        "ClearanceCertificate",
        foreign_keys="ClearanceCertificate.issued_by",
        back_populates="issuer"
    )

    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Role(BaseModel):
    __tablename__ = 'roles'
    name = Column(Enum(RoleEnum), unique=True, nullable=False)
    description = Column(Text)
    
    # Relationships
    users = relationship("User", back_populates="role")

class Department(BaseModel):
    __tablename__ = 'departments'
    name = Column(String(100), nullable=False)
    utility = Column(Boolean, nullable=False, default=False)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(Integer, ForeignKey('sessions.id', ondelete='SET NULL'))
    
    # Relationships
    organization = relationship("Organization", back_populates="departments")
    session = relationship("Session", back_populates="departments")
    users = relationship("User", back_populates="department")
    levels = relationship("Level", back_populates="department", cascade="all, delete-orphan")
    payment_items = relationship("PaymentItem", back_populates="department", cascade="all, delete-orphan")
    clearance_items = relationship("ClearanceItem", back_populates="department", cascade="all, delete-orphan")
    clearance_certificates = relationship("ClearanceCertificate", back_populates="department")
    clearances = relationship("Clearance", back_populates="department")
    
    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='unique_dept_per_org'),
    )

class Level(BaseModel):
    __tablename__ = 'levels'
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Foreign keys
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(Integer, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    department = relationship("Department", back_populates="levels")
    session = relationship("Session", back_populates="levels")
    users = relationship("User", back_populates="level")
    payment_items = relationship("PaymentItem", back_populates="level")
    clearance_items = relationship("ClearanceItem", back_populates="level")
    
    __table_args__ = (
        UniqueConstraint('name', 'department_id', 'session_id', name='unique_level_per_dept_session'),
    )

class Session(BaseModel):
    __tablename__ = 'sessions'
    name = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=False)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="sessions")
    departments = relationship("Department", back_populates="session")
    levels = relationship("Level", back_populates="session")
    payment_items = relationship("PaymentItem", back_populates="academic_session")
    clearance_items = relationship("ClearanceItem", back_populates="academic_session")
    clearances = relationship("Clearance", back_populates="academic_session")
    
    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='unique_session_per_org'),
        CheckConstraint('end_date >= start_date', name='check_dates'),
    )

class PaymentItem(BaseModel):
    __tablename__ = 'payment_items'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    account_name = Column(String(255), nullable=False)
    business_name = Column(String(255), nullable=False)
    subaccount_code = Column(String(255), nullable=False)
    bank_name = Column(String(255), nullable=False)
    account_number = Column(String(255), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    percentage_charge = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    academic_session_id = Column(Integer, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    level_id = Column(Integer, ForeignKey('levels.id', ondelete='CASCADE'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="payment_items")
    academic_session = relationship("Session", back_populates="payment_items")
    level = relationship("Level", back_populates="payment_items")
    department = relationship("Department", back_populates="payment_items")
    payments = relationship("Payment", back_populates="payment_item", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('amount >= 0', name='check_amount'),
        UniqueConstraint('name', 'department_id', 'level_id', name='unique_payment_per_dept_level'),
    )

class Payment(BaseModel):
    __tablename__ = 'payments'
    amount = Column(DECIMAL(10, 2), nullable=False)
    payment_reference = Column(String(255), nullable=False, unique=True, index=True)
    transaction_id = Column(String(255))
    payment_method = Column(String(20), nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    url = Column(String(255), unique=True)
    payment_date = Column(TIMESTAMP, default=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    payment_item_id = Column(Integer, ForeignKey('payment_items.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    payment_item = relationship("PaymentItem", back_populates="payments")
    clearance_certificate = relationship("ClearanceCertificate", back_populates="payment", uselist=False)
    
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_payment_amount'),
    )

class Clearance(BaseModel):
    __tablename__ = "clearance"
    name = Column(String(255), nullable=False)
    file_url = Column(String(255))
    status = Column(Enum(ClearanceStatus), nullable=False, default=ClearanceStatus.NOTCLEARED)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True)
    academic_session_id = Column(Integer, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    clearance_item_id = Column(Integer, ForeignKey('clearance_items.id', ondelete='CASCADE'), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="clearance_items")
    academic_session = relationship("Session", back_populates="clearances")
    department = relationship("Department", back_populates="clearances")
    user = relationship("User", back_populates="clearances")
    clearance_items = relationship("ClearanceItem", back_populates="clearance")

    def to_dict(self):
        return {'id': self.id, 
        'name': self.name,
        'file_url':self.file_url,
        'organization_id':self.organization_id,
        'clearance_item_id':self.clearance_item_id,
        'department_id':self.department_id,
        'user_id':self.user_id
        }

class ClearanceItem(BaseModel):
    __tablename__ = 'clearance_items'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Foreign keys
    academic_session_id = Column(Integer, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=True)
    level_id = Column(Integer, ForeignKey('levels.id', ondelete='CASCADE'), nullable=True)
    
    # Relationships
    clearance = relationship("Clearance", back_populates="clearance_items",cascade="all, delete-orphan")
    academic_session = relationship("Session", back_populates="clearance_items")
    department = relationship("Department", back_populates="clearance_items")
    level = relationship("Level", back_populates="clearance_items")

    def to_dict(self):
        return {'id': self.id, 'name': self.name,'department_id':self.department_id}

class ClearanceCertificate(BaseModel):
    __tablename__ = 'clearance_certificates'
    certificate_number = Column(String(255), nullable=False, unique=True, index=True)
    certificate_path = Column(String(255), nullable=False)
    issued_at = Column(TIMESTAMP, default=func.now())
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    
    # Foreign keys
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    issued_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    payment_id = Column(Integer, ForeignKey('payments.id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    department = relationship("Department", back_populates="clearance_certificates")
    user = relationship("User", foreign_keys=[user_id], back_populates="clearance_certificates_owned")
    issuer = relationship("User", foreign_keys=[issued_by], back_populates="clearance_certificates_issued")
    payment = relationship("Payment", back_populates="clearance_certificate")

# Create tables for the models
with app.app_context():
    db.create_all()

# Route to add a new department
@app.route("/departments/add", methods=['POST', 'GET'])
def add_dept():
    if request.method == 'POST':
        data = request.get_json()  # Get JSON data from the request body
        new_dept = Department(name=data['name'])  # Create a new department
        db.session.add(new_dept)  # Add department to session
        db.session.commit()  # Commit the transaction to the database
        return jsonify({'message': 'Department Created', 'department': new_dept.to_dict()}), 201

# Route to get all departments
@app.route("/departments/all", methods=['POST', 'GET'])
def get_all_dept():
    if request.method == 'GET':
        depts = Department.query.all()  # Query all departments
        return jsonify([dept.to_dict() for dept in depts]), 200

@app.route("/clearance_items/create",methods=['POST'])#create clearance item
def add_clearance_item():
    if request.method=='POST':
        data=request.get_json()
        clearance_item=ClearanceItem(name=data['name'],description=data['desc'],academic_session_id=data['session'],department_id=data['department_id'],level_id=data['level_id'])
        db.session.add(clearance_item)
        db.session.commit()
        return jsonify({'message': 'Clearance Item Created', 'Item': clearance_item.to_dict()}), 201
    
@app.route("/clearance_items/all", methods=['POST', 'GET'])#all clearance items
def get_all_clearance_items():
    if request.method == 'GET':
        depts = ClearanceItem.query.all()
        return jsonify([dept.to_dict() for dept in depts]), 200

@app.route("/clearance_items/student", methods=['POST', 'GET'])#filter clearance items for student based on department id,session id and level id
def get_all_clearance_items_student():
    if request.method == 'GET':
        data=request.get_json()
        depts = ClearanceItem.query.filter(
            (ClearanceItem.department_id==data['department_id']) & 
            (ClearanceItem.academic_session_id==data['session']) & 
            (ClearanceItem.level_id==data['level_id'])
        ).all() # Query filtered Clearance Items for student
        return jsonify([dept.to_dict() for dept in depts]), 200

@app.route("/clearance_items/delete", methods=['POST', 'GET'])#delete clearance item
def Delete_clearance_items():
    if request.method == 'POST':
        data=request.get_json()
        dept = ClearanceItem.query.get_or_404(data['id'])# Delete Clearance Item
        db.session.delete(dept)
        db.session.commit()
        return jsonify({'message':'Successfully Deleted Clearance Item','Clearance Item':dept.to_dict()}),201

@app.route("/clearance/create",methods=['POST'])#make clearance request for student
def add_clearance():
    if request.method=='POST':
        data=request.get_json()
        clearance_item=Clearance(
            name=data['name'],
            file_url=data['file'],
            organization_id=data['organization_id'],
            academic_session_id=data['session'],
            department_id=data['department_id'],
            user_id=data['user_id'],
            clearance_item_id=data['clearance_item_id'],
            )
        db.session.add(clearance_item)
        db.session.commit()
        return jsonify({'message': 'Clearance Created', 'Item': clearance_item.to_dict()}), 201

@app.route("/clearance/all", methods=['POST', 'GET']) # all clearance requests
def get_all_clearance_req():
    if request.method == 'GET':
        depts = Clearance.query.all()
        return jsonify([dept.to_dict() for dept in depts]), 200

@app.route("/clearance/subadmin", methods=['POST', 'GET']) #Query all clearance request for sub admin based on departnment id , session, organization and status(not cleared)
def get_all_clearance_subadmin():
    if request.method == 'GET':
        data=request.get_json()
        depts = Clearance.query.filter(
            (Clearance.department_id==data['department_id']) & 
            (Clearance.academic_session_id==data['session']) & 
            (Clearance.organization_id==data['organization_id']) &
            (Clearance.status==ClearanceStatus.NOTCLEARED)
        ).all() 
        return jsonify([dept.to_dict() for dept in depts]), 200

@app.route("/clearance/student", methods=['POST', 'GET'])# Query clearnce request for student based on user id
def get_all_clearance_student():
    if request.method == 'GET':
        data=request.get_json()
        depts = Clearance.query.filter(
            (Clearance.user_id==data['user_id']) # add (Clearance.status==ClearanceStatus.NOTCLEARED)
        ).all() 
        return jsonify([dept.to_dict() for dept in depts]), 200



@app.route("/clearance/clear", methods=['POST', 'GET']) #Clear a student
def Clear():
    if request.method == 'POST':
        data=request.get_json()
        dept = Clearance.query.get_or_404(data['id'])# Delete Clearance Item
        dept.status=ClearanceStatus.ISSUED
        db.session.commit()
        return jsonify({'message':'Successfully Deleted Clearance Item','Clearance Item':dept.to_dict()}),201


if __name__ == '__main__':
    app.run()
