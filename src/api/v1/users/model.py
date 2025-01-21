from sqlalchemy import Column, String, Table, Text, ForeignKey, Integer, Enum, DECIMAL, CheckConstraint, Boolean, UniqueConstraint, Date, TIMESTAMP, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from api.base.model import BaseModel
from enum import Enum as PyEnum
import datetime
from api.base.model import BaseModel
# Enums
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

# Models
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

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "acronym": self.acronym,
            "phone": self.phone,
            "address": self.address,
            "email": self.email,
        }
    
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'matric_number': self.matric_number,
            'faculty': self.faculty,
            'campus': self.campus,
            'residential_address': self.residential_address,
            'phone': self.phone,
            'role_id': self.role_id,
            'organization_id': self.organization_id,
            'department_id': self.department_id,
            'level_id': self.level_id
        }
    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Role(BaseModel):
    __tablename__ = 'roles'
    name = Column(Enum(RoleEnum), unique=True, nullable=False)
    description = Column(Text)
    
    # Relationships
    users = relationship("User", back_populates="role")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'utility': self.utility,
            'organization_id': self.organization_id,
            'session_id': self.session_id,
        }

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'department_id': self.department_id,
            'session_id': self.session_id,
        }

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'is_active': self.is_active,
            'organization_id': self.organization_id,
        }

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'account_name': self.account_name,
            'business_name': self.business_name,
            'subaccount_code': self.subaccount_code,
            'bank_name': self.bank_name,
            'account_number': self.account_number,
            'amount': self.amount,
            'percentage_charge': self.percentage_charge,
            'is_active': self.is_active,
            'organization_id': self.organization_id,
            'academic_session_id': self.academic_session_id,
            'level_id': self.level_id,
            'department_id': self.department_id,
        }

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'payment_reference': self.payment_reference,
            'transaction_id': self.transaction_id,
            'payment_method': self.payment_method,
            'status': self.status,
            'url': self.url,
            'payment_date': self.payment_date,
            'user_id': self.user_id,
            'payment_item_id': self.payment_item_id,
        }

class Clearance(BaseModel):
    __tablename__ = "clearance"
    name = Column(String(255), nullable=False)
    file_url = Column(String(255))
    status = Column(Enum(ClearanceStatus), nullable=False, default=ClearanceStatus.NOTCLEARED)
    
    # Foreign keys
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    academic_session_id = Column(Integer, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    clearance_item_id = Column(Integer, ForeignKey('clearance_items.id', ondelete='CASCADE'), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="clearance_items")
    academic_session = relationship("Session", back_populates="clearances")
    department = relationship("Department", back_populates="clearances")
    user = relationship("User", back_populates="clearances")
    clearance_items = relationship("ClearanceItem", back_populates="clearance", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'file_url': self.file_url,
            'status': self.status,
            'organization_id': self.organization_id,
            'academic_session_id': self.academic_session_id,
            'department_id': self.department_id,
            'user_id': self.user_id,
            'clearance_item_id': self.clearance_item_id,
        }

class ClearanceItem(BaseModel):
    __tablename__ = 'clearance_items'
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Foreign keys
    academic_session_id = Column(Integer, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    level_id = Column(Integer, ForeignKey('levels.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    clearance = relationship("Clearance", back_populates="clearance_items")
    academic_session = relationship("Session", back_populates="clearance_items")
    department = relationship("Department", back_populates="clearance_items")
    level = relationship("Level", back_populates="clearance_items")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'academic_session_id': self.academic_session_id,
            'department_id': self.department_id,
            'level_id': self.level_id,
        }

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'certificate_number': self.certificate_number,
            'certificate_path': self.certificate_path,
            'issued_at': self.issued_at,
            'status': self.status,
            'department_id': self.department_id,
            'user_id': self.user_id,
            'issued_by': self.issued_by,
            'payment_id': self.payment_id,
        }
