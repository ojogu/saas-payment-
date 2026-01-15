# from datetime import datetime

# from werkzeug.security import check_password_hash, generate_password_hash


# class User(BaseModel):
#     __tablename__ = "users"
#     id = db.Column(db.Integer, primary_key=True)
#     firstname = db.Column(db.String(80), nullable=False)
#     lastname = db.Column(db.String(80), nullable=False)
#     middlename = db.Column(db.String(80), nullable=True)
#     email = db.Column(db.String(120), nullable=True)
#     matric_number = db.Column(db.String(50), nullable=True, unique=True)
#     phone_number = db.Column(db.String(50), nullable=True)
#     level = db.Column(db.String(20), nullable=True)
#     password_hash = db.Column(db.String(128), nullable=False)
#     role = db.Column(db.String(20), nullable=False)
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=True
#     )
#     faculty_id = db.Column(db.Integer, db.ForeignKey("faculties.id"), nullable=True)
#     department_id = db.Column(
#         db.Integer, db.ForeignKey("departments.id"), nullable=True
#     )
#     clearance_point_id = db.Column(
#         db.Integer, db.ForeignKey("clearance_points.id"), nullable=True, default=None
#     )
#     created_at = db.Column(db.DateTime, default=datetime.now())
#     organization = db.relationship("Organization", back_populates="users")
#     faculty = db.relationship("Faculty", back_populates="users")
#     department = db.relationship("Department", back_populates="users")
#     clearance_point = db.relationship("ClearancePoint", back_populates="users")
#     clearances = db.relationship(
#         "Clearance", back_populates="user", cascade="all, delete-orphan"
#     )
#     payments = db.relationship(
#         "Payment", back_populates="user", cascade="all, delete-orphan"
#     )
#     passport = db.relationship(
#         "PassPorts", back_populates="user", cascade="all, delete-orphan"
#     )

#     def set_password(self, password):
#         self.password_hash = generate_password_hash(
#             password, method="pbkdf2:sha256", salt_length=12
#         )

#     def check_password(self, password):
#         return check_password_hash(self.password_hash, password)


# class Organization(BaseModel):
#     __tablename__ = "organizations"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120), nullable=False, unique=True)
#     phone = db.Column(db.String(120), nullable=True, unique=True)
#     logo = db.Column(db.String(120), nullable=True, unique=True)
#     email = db.Column(db.String(120), nullable=True, unique=True)
#     address = db.Column(db.String(120), nullable=True, unique=True)
#     slogan = db.Column(db.String(120), nullable=True, unique=True)
#     users = db.relationship(
#         "User", back_populates="organization", cascade="all, delete-orphan"
#     )
#     departments = db.relationship(
#         "Department",
#         back_populates="organization",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )
#     department_codes = db.relationship(
#         "DepartmentCode",
#         back_populates="organization",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )
#     clearance_points = db.relationship(
#         "ClearancePoint",
#         back_populates="organization",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )
#     clearance_logs = db.relationship(
#         "ClearanceLogs",
#         back_populates="organization",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )
#     faculties = db.relationship(
#         "Faculty",
#         back_populates="organization",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )
#     clearance_items = db.relationship(
#         "ClearanceItem",
#         back_populates="organization",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )
#     accounts = db.relationship(
#         "Accounts",
#         back_populates="organization",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )
#     sessions = db.relationship(
#         "Session",
#         back_populates="organization",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )


# class Notification_Setting(BaseModel):
#     __tablename__ = "notification_settings"
#     id = db.Column(db.Integer, primary_key=True)
#     price = db.Column(db.Integer, nullable=False)
#     account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=True)
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=False
#     )


# class User_Notification(BaseModel):
#     __tablename__ = "use_notifications"
#     id = db.Column(db.Integer, primary_key=True)
#     student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     email = db.Column(db.String(120), nullable=False, unique=True)
#     phone = db.Column(db.String(120), nullable=False, unique=True)
#     last_paid_at = db.Column(db.DateTime, default=datetime.now())


# class Faculty(BaseModel):
#     __tablename__ = "faculties"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120), nullable=False)
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=False
#     )
#     organization = db.relationship("Organization", back_populates="faculties")
#     users = db.relationship(
#         "User", back_populates="faculty", lazy=True, cascade="all, delete-orphan"
#     )
#     departments = db.relationship(
#         "Department", back_populates="faculty", lazy=True, cascade="all, delete-orphan"
#     )


# class Department(BaseModel):
#     __tablename__ = "departments"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120), nullable=False)
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=False
#     )
#     organization = db.relationship("Organization", back_populates="departments")
#     faculty_id = db.Column(db.Integer, db.ForeignKey("faculties.id"), nullable=False)
#     faculty = db.relationship("Faculty", back_populates="departments")
#     users = db.relationship(
#         "User", back_populates="department", lazy=True, cascade="all, delete-orphan"
#     )
#     department_code = db.relationship("DepartmentCode", back_populates="department")
#     multi_clearance_items = db.relationship(
#         "MultiClearanceItem",
#         back_populates="department",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )


# class DepartmentCode(BaseModel):
#     __tablename__ = "department_code"
#     id = db.Column(db.Integer, primary_key=True)
#     code = db.Column(db.String(10), nullable=False)
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=False
#     )
#     organization = db.relationship("Organization", back_populates="department_codes")
#     department_id = db.Column(
#         db.Integer, db.ForeignKey("departments.id"), nullable=False
#     )
#     department = db.relationship("Department", back_populates="department_code")


# class ClearancePoint(BaseModel):
#     __tablename__ = "clearance_points"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120), nullable=False)
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=False
#     )
#     organization = db.relationship("Organization", back_populates="clearance_points")
#     account_points = db.relationship(
#         "AccountPoints",
#         back_populates="clearance_point",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )
#     users = db.relationship(
#         "User",
#         back_populates="clearance_point",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )
#     clearance_items = db.relationship(
#         "ClearanceItem",
#         back_populates="clearance_point",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )


# class ClearanceItem(BaseModel):
#     __tablename__ = "clearance_items"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120), nullable=False)
#     desc = db.Column(db.String(250), nullable=False)
#     is_global = db.Column(db.Boolean, default=False)
#     payment_required = db.Column(db.Boolean, nullable=False, default=False)
#     document_required = db.Column(db.Boolean, nullable=False, default=False)
#     is_multi = db.Column(db.Boolean, nullable=False, default=False)
#     is_passive = db.Column(db.Boolean, nullable=False, default=False)
#     amount = db.Column(db.Float, nullable=True)
#     all_level = db.Column(db.Boolean, nullable=False, default=False)
#     multi_levels = db.relationship(
#         "MultiLevel", back_populates="clearance_item", cascade="all, delete-orphan"
#     )
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=False
#     )
#     clearance_point_id = db.Column(
#         db.Integer, db.ForeignKey("clearance_points.id"), nullable=False
#     )
#     session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
#     account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=True)
#     organization = db.relationship("Organization", back_populates="clearance_items")
#     clearance_point = db.relationship(
#         "ClearancePoint", back_populates="clearance_items"
#     )
#     clearances = db.relationship(
#         "Clearance", back_populates="clearance_item", cascade="all, delete-orphan"
#     )
#     passive_payments = db.relationship(
#         "PassivePayment", back_populates="clearance_item", cascade="all, delete-orphan"
#     )
#     multi_clearance_items = db.relationship(
#         "MultiClearanceItem",
#         back_populates="clearance_item",
#         cascade="all, delete-orphan",
#     )
#     clearance_officers = db.relationship(
#         "ClearanceOfficers",
#         back_populates="clearance_item",
#         cascade="all, delete-orphan",
#     )
#     session = db.relationship("Session", back_populates="clearance_items")
#     account = db.relationship("Accounts", back_populates="clearance_items")


# class ClearanceItemEdit(BaseModel):
#     __tablename__ = "clearance_item_edit"
#     item_id = db.Column(db.Integer, db.ForeignKey("clearance_items.id"), nullable=True)
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120), nullable=False)
#     desc = db.Column(db.String(250), nullable=False)
#     is_global = db.Column(db.Boolean, default=False)
#     payment_required = db.Column(db.Boolean, nullable=False, default=False)
#     document_required = db.Column(db.Boolean, nullable=False, default=False)
#     is_multi = db.Column(db.Boolean, nullable=False, default=False)
#     is_passive = db.Column(db.Boolean, nullable=False, default=False)
#     amount = db.Column(db.Float, nullable=True)
#     all_level = db.Column(db.Boolean, nullable=False, default=False)
#     multi_edits = db.Column(db.JSON)
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=False
#     )
#     clearance_point_id = db.Column(
#         db.Integer, db.ForeignKey("clearance_points.id"), nullable=False
#     )
#     session_id = db.Column(db.Integer)
#     account_id = db.Column(db.Integer)


# class ClearanceOfficers(BaseModel):
#     __tablename__ = "clearance_officers"
#     id = db.Column(db.Integer, primary_key=True)
#     officer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     clearance_item_id = db.Column(
#         db.Integer, db.ForeignKey("clearance_items.id"), nullable=False
#     )
#     clearance_item = db.relationship(
#         "ClearanceItem", back_populates="clearance_officers"
#     )


# class MultiClearanceItem(BaseModel):
#     __tablename__ = "multi_clearance_item"
#     id = db.Column(db.Integer, primary_key=True)
#     clearance_item_id = db.Column(
#         db.Integer, db.ForeignKey("clearance_items.id"), nullable=False
#     )
#     department_id = db.Column(
#         db.Integer, db.ForeignKey("departments.id"), nullable=False
#     )
#     department = db.relationship("Department", back_populates="multi_clearance_items")
#     clearance_item = db.relationship(
#         "ClearanceItem", back_populates="multi_clearance_items"
#     )


# class MultiLevel(BaseModel):
#     __tablename__ = "multi_levels"
#     id = db.Column(db.Integer, primary_key=True)
#     clearance_item_id = db.Column(
#         db.Integer, db.ForeignKey("clearance_items.id"), nullable=False
#     )
#     clearance_item = db.relationship("ClearanceItem", back_populates="multi_levels")
#     level = db.Column(db.String(20), nullable=True)


# class ClearanceDocuments(BaseModel):
#     __tablename__ = "clearance_document"
#     id = db.Column(db.Integer, primary_key=True)
#     desc = db.Column(db.String(250), nullable=False)
#     clearance_item_id = db.Column(
#         db.Integer, db.ForeignKey("clearance_items.id"), nullable=False
#     )


# class Accounts(BaseModel):
#     __tablename__ = "accounts"
#     id = db.Column(db.Integer, primary_key=True)
#     subaccount = db.Column(db.String(120), nullable=True)
#     account_number = db.Column(db.String(120), nullable=True)
#     account_name = db.Column(db.String(120), nullable=True)
#     bank = db.Column(db.String(120), nullable=True)
#     bank_name = db.Column(db.String(120), nullable=True)
#     default_account = db.Column(db.Boolean, default=False)
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=False
#     )
#     organization = db.relationship("Organization", back_populates="accounts")
#     account_points = db.relationship(
#         "AccountPoints", back_populates="account", cascade="all, delete-orphan"
#     )
#     clearance_items = db.relationship(
#         "ClearanceItem",
#         back_populates="account",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )


# class AccountPoints(BaseModel):
#     __tablename__ = "account_points"
#     id = db.Column(db.Integer, primary_key=True)
#     clearance_point_id = db.Column(
#         db.Integer, db.ForeignKey("clearance_points.id"), nullable=False
#     )
#     clearance_point = db.relationship("ClearancePoint", back_populates="account_points")
#     account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=True)
#     account = db.relationship("Accounts", back_populates="account_points")


# class Files(BaseModel):
#     __tablename__ = "files"
#     id = db.Column(db.Integer, primary_key=True)
#     clearance_id = db.Column(db.Integer, db.ForeignKey("clearances.id"), nullable=True)
#     file_url = db.Column(db.String(250), nullable=True, unique=True)
#     desc = db.Column(db.String(250), nullable=False)
#     clearance = db.relationship("Clearance", back_populates="files")


# class PassPorts(BaseModel):
#     __tablename__ = "passports"
#     id = db.Column(db.Integer, primary_key=True)
#     student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     file_url = db.Column(db.String(250), nullable=True, unique=False)
#     user = db.relationship("User", back_populates="passport")


# # class PaymentItem(BaseModel):
# #     __tablename__="payment_items"
# #     id=db.Column(db.Integer,primary_key=True)
# #     name=db.Column(db.String(120),nullable=False, unique=True)
# #     amount=db.Column(db.Float,nullable=False)
# #     balance=db.Column(db.Float,nullable=False, default=0.0)
# #     is_global=db.Column(db.Boolean, default=False)
# #     level=db.Column(db.String(20),nullable=True)
# #     account_number=db.Column(db.String(80),nullable=False)
# #     account_name=db.Column(db.String(120),nullable=False)
# #     organization_id=db.Column(db.Integer,db.ForeignKey("organizations.id"), nullable=False)
# #     department_id=db.Column(db.Integer,db.ForeignKey("departments.id"), nullable=False)
# #     organization=db.relationship('Organization',back_populates='payment_items')
# #     department=db.relationship('Department',back_populates='payment_items')
# #     payments=db.relationship('Payment',back_populates='payment_item')


# class Payment(BaseModel):
#     __tablename__ = "payments"
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     status = db.Column(db.String(20), default="pending")
#     amount = db.Column(db.Float, nullable=False)
#     payment_ref = db.Column(db.String(50), unique=True, nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.now())
#     user = db.relationship("User", back_populates="payments")
#     clearance = db.relationship("Clearance", back_populates="payment")
#     system_payment = db.Column(db.Boolean, nullable=True, default=False)


# class PassivePayment(BaseModel):
#     __tablename__ = "passive_payments"
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     payment_ref = db.Column(db.String(50), unique=True, nullable=False)
#     amount = db.Column(db.Float, nullable=False)
#     clearance_item_id = db.Column(
#         db.Integer, db.ForeignKey("clearance_items.id"), nullable=False
#     )
#     clearance_item = db.relationship("ClearanceItem", back_populates="passive_payments")


# class Clearance(BaseModel):
#     __tablename__ = "clearances"
#     id = db.Column(db.Integer, primary_key=True)
#     student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     clearance_item_id = db.Column(
#         db.Integer, db.ForeignKey("clearance_items.id"), nullable=False
#     )
#     status = db.Column(db.String(20), default="pending")
#     payment_id = db.Column(db.Integer, db.ForeignKey("payments.id"), nullable=True)
#     created_at = db.Column(db.DateTime, default=datetime.now())
#     remark = db.Column(db.String(255), default="No remark")
#     user = db.relationship("User", back_populates="clearances")
#     payment = db.relationship("Payment", back_populates="clearance")
#     files = db.relationship(
#         "Files", back_populates="clearance", cascade="all, delete-orphan"
#     )
#     clearance_item = db.relationship("ClearanceItem", back_populates="clearances")


# class ClearanceLogs(BaseModel):
#     __tablename__ = "clearance_logs"
#     id = db.Column(db.Integer, primary_key=True)
#     action = db.Column(db.String(255), nullable=False)
#     email = db.Column(db.String(255), nullable=True)
#     matric = db.Column(db.String(255), nullable=True)
#     role = db.Column(db.String(255), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.now())
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=False
#     )
#     organization = db.relationship("Organization", back_populates="clearance_logs")


# class Session(BaseModel):
#     __tablename__ = "sessions"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50), nullable=False)
#     start_year = db.Column(db.Integer, nullable=False)
#     end_year = db.Column(db.Integer, nullable=False)
#     is_active = db.Column(db.Boolean, default=False)
#     organization_id = db.Column(
#         db.Integer, db.ForeignKey("organizations.id"), nullable=False
#     )
#     organization = db.relationship("Organization", back_populates="sessions")
#     clearance_items = db.relationship(
#         "ClearanceItem",
#         back_populates="session",
#         lazy=True,
#         cascade="all, delete-orphan",
#     )
