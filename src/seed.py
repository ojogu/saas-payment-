from utils.dependency import db 
from app import create_app
from sqlalchemy import inspect, text
from api.v1.users.model import Role, RoleEnum, Level, User, Department, PaymentItem, Session, Payment, TransactionStatus, Organization
from sqlalchemy.exc import SQLAlchemyError
from api.v1.users.model import User
from sqlalchemy import true

app = create_app()

def seed_database():
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()  # Start a transaction
        try:
            # Drop all tables with CASCADE
            connection.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
            db.create_all()  # Create tables
            transaction.commit()  # Commit if successful
        except Exception as e:
            transaction.rollback()  # Roll back if any error occurs
            print(f"Error occurred: {e}")
        finally:
            connection.close()
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print("Tables in the database:", tables)

# Call the function
# seed_database()


def seed_roles():
    with app.app_context():
        roles = [
            # {"name": RoleEnum.ADMIN, "description": "Administrator with full access"},
            {"name": RoleEnum.SUBADMIN, "description": "Sub-administrator with limited access"},
            {"name": RoleEnum.BURSAR, "description": "Bursar responsible for financial operations"},
            {"name": RoleEnum.STUDENT, "description": "Student with access to student-specific features"}
        ]

        try:
            for role_data in roles:
                role = Role(**role_data)
                db.session.add(role)
            db.session.commit()
            print("Roles seeded successfully.")
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error seeding roles: {e}")

# Call the function
# seed_roles()

def fetch_all_roles():
    with app.app_context():
        try:
            roles = db.session.query(Role).all()
            role_list = [{"name": role.name, "description": role.description} for role in roles]
            print("Roles:", role_list)
            return role_list
        except SQLAlchemyError as e:
            print(f"Error fetching roles: {e}")
            return []

fetch_all_roles()

# Raw SQL to fetch enum values
def fetch_enum_values():
    sql = db.text("SELECT unnest(enum_range(NULL::roleenum))")
    with app.app_context():
        try:
            result = db.session.execute(sql)
            enum_values = [row[0] for row in result]  # Extract values from the result
            print("Enum values:", enum_values)
        except Exception as e:
            print("Error:", e)
        finally:
            db.session.close()
            

def seed_level():
    with app.app_context():
        levels = [
            {"name": "100", "description": "100 level"},
            {"name": "200", "description": "200 level"},
            {"name": "300", "description": "300 level"},
            {"name": "400", "description": "400 level"},
            {"name": "500", "description": "500 level"}
        ]
        try:
            for level_data in levels:
                level = Level(**level_data)
                db.session.add(level)
            db.session.commit()
            print("Levels seeded successfully.")
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error seeding levels: {e}")

# seed_level()

def query_all_levels():
    with app.app_context():
        try:
            levels = Level.query.all()
            for level in levels:
                print(f"Level: {level.name}, Description: {level.description}")
        except SQLAlchemyError as e:
            print(f"Error querying levels: {e}")

# Call the function
# query_all_levels()

def query_user_by_id(entity_id):
    with app.app_context():
        try:
            user = User.query.filter_by(entity_id=entity_id).first()
            if user:
                print(f"User found: {user}")
            else:
                print("User not found.")
        except SQLAlchemyError as e:
            print(f"Error querying user: {e}")

# Call the function
# query_user_by_id("52a4fd48-80f2-43a7-8293-5672bca672af")

def query_payment_items_by_org(organization_acronym):
    with app.app_context():
        """Query all payment items in an organization"""
        query = db.session.query(PaymentItem).join(Organization).filter(
            Organization.acronym == organization_acronym
        )
        return query.all()

# Call the function
# print (query_payment_items_by_org("unical"))

def query_payment_items_department(organization_acronym, department_name):
    with app.app_context():
        """Query all payment items for a department in an organization"""
        query = db.session.query(PaymentItem).join(Organization).join(Department).filter(
            Organization.acronym == organization_acronym,
            Department.name == department_name
        ).filter(PaymentItem.department_id == Department.id)
        return query.all()
# # Call the function
# print(query_payment_items_department("unical", "computer science"))

def query_payment_items_department_level(organization_acronym, department_name, level_name):
    with app.app_context():
        """Query all payment items for a department in an organization"""
        query = (
            db.session.query(PaymentItem)
            .join(Department, PaymentItem.department_id == Department.id)
            .join(Level, PaymentItem.level_id == Level.id)
            .join(Organization, Department.organization_id == Organization.id)
            .filter(
                Organization.acronym == organization_acronym,
                Department.name == department_name,
                Level.name == level_name,
            )
        )
        result = query.all()
        if not result:
            print(f"No payment items found for organization: {organization_acronym}, department: {department_name}, level: {level_name}")
        return result

# # Call the function
# print(query_payment_items_department_level("unical", "physics", "200"))



def seed_payment_item(organization_acronym, department_name, level_name, payment_item_name, payment_item_amount, academic_session_name):
    with app.app_context():
        """Seed payment item for an organization, department and level"""
        organization = Organization.query.filter_by(acronym=organization_acronym).first()
        if organization:
            department = Department.query.filter_by(name=department_name, organization=organization).first()
            if department:
                level = Level.query.filter_by(name=level_name).first()
                if level:
                    academic_session = Session.query.filter_by(name=academic_session_name, organization=organization).first()
                    if academic_session:
                        payment_item = PaymentItem(
                            name=payment_item_name,
                            amount=payment_item_amount,
                            organization=organization,
                            department=department,
                            level=level,
                            academic_session=academic_session
                        )
                        db.session.add(payment_item)
                        db.session.commit()
                        print(f"Payment item seeded: {payment_item_name}, {payment_item_amount}, {level_name}, {department_name}, {organization_acronym}")
                    else:
                        print(f"Academic session not found: {academic_session_name}")
                else:
                    print(f"Level not found: {level_name}")
            else:
                print(f"Department not found: {department_name}")
        else:
            print(f"Organization not found: {organization_acronym}")

# Call the function
# seed_payment_item("unical", "physics", "200", "GSS", 20000, "2023/2024 Academic Year")

def delete_payment_item(organization_acronym, department_name, payment_item_name, level_name):
    
    with app.app_context():
        """Delete a payment item based on organization, department, payment item name, and level"""
        payment_item = db.session.query(PaymentItem).join(Level).join(Department).join(Organization).filter(
            Organization.acronym == organization_acronym,
            Department.name == department_name,
            PaymentItem.name == payment_item_name,
            Level.name == level_name
        ).first()

        if payment_item:
            db.session.delete(payment_item)
            db.session.commit()
            print(f"Payment item deleted: {payment_item_name}, {level_name}, {department_name}, {organization_acronym}")
        else:
            print("Payment item not found.")

# Call the function
# delete_payment_item("unical", "computer science", "School fees", '100')

def drop_and_create():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Tables created:", inspect(db.engine).get_table_names())

# drop_and_create()

def query_payment_items():
    with app.app_context():
        """Query the payment item table and print all the columns"""
        payment_items = db.session.query(PaymentItem).all()
        for item in payment_items:
            print(f"Name: {item.name}, Amount: {item.amount}, Level: {item.level.name}, Department: {item.department.name}, Organization: {item.organization.acronym}, Academic Session: {item.academic_session.name}")

# Call the function
# query_payment_items()


def fetch_specific_payment_item(item_name, organization_acronym, department_name, level_name):
    with app.app_context():
        """Fetch a specific payment item from an organization, department, and level"""
        query = (
            db.session.query(PaymentItem)
            .join(Department, PaymentItem.department_id == Department.id)
            .join(Level, PaymentItem.level_id == Level.id)
            .join(Organization, Department.organization_id == Organization.id)
            .filter(
                PaymentItem.name.ilike(f"%{item_name}%"),
                Organization.acronym == organization_acronym,
                Department.name.ilike(f"%{department_name}%"),
                Level.name.ilike(f"%{level_name}%"),
            )
            .options(
                db.joinedload(PaymentItem.organization),  # Eagerly load `organization`
                db.joinedload(PaymentItem.department),    # Eagerly load `department`
                db.joinedload(PaymentItem.level),         # Eagerly load `level`
            )
        )
        result = query.first()
        if not result:
            print(
                f"No payment item '{item_name}' found for organization: {organization_acronym}, "
                f"department: {department_name}, level: {level_name}"
            )
        return result

# Call the function
# print (fetch_specific_payment_item("school fees", "unical", "computer science", "200"))

def query_payment_items_by_session(session_name, organization_acronym, department_name, level_name):
    with app.app_context():
        """Query the payment item table based on the session name, organization, department, and level"""
        query = (
            db.session.query(PaymentItem)
            .join(Department, PaymentItem.department_id == Department.id)
            .join(Level, PaymentItem.level_id == Level.id)
            .join(Organization, Department.organization_id == Organization.id)
            .join(Session, PaymentItem.academic_session_id == Session.id)
            .filter(
                Session.name.ilike(f"%{session_name}%"),
                Organization.acronym == organization_acronym,
                Department.name.ilike(f"%{department_name}%"),
                Level.name.ilike(f"%{level_name}%"),
            )
        )
        return query.all()

# print(query_payment_items_by_session("2023/2024 Academic Year", "unical", "computer science", "200"))


def fetch_payments(organization_acronym, department_name, level_name, session_name, user_id):
    with app.app_context():
        """Fetch payments for a particular organization, department, level, session, and user_id"""
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
            )
            .add_columns(User.email)
        )
        return query.all()

# Call the function
# print(fetch_payments(organization_acronym="unical", department_name="computer science", level_name="200", session_name="2023/2024 Academic Year", user_id=4))


def fetch_pending_payments(organization_acronym, department_name, level_name, session_name, user_id):
    with app.app_context():
        """Fetch payments with status pending for a particular organization, department, level, session, and user_id"""
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
        return query.all()

# Call the function
# print(fetch_pending_payments(organization_acronym="unical", department_name="computer science", level_name="200", session_name="2023/2024 Academic Year", user_id=4))

def fetch_paid_payments(user_id):
    with app.app_context():
        user = User.query.get(user_id)
        organization_acronym = user.organization.acronym
        department_name = user.department.name
        level_name = user.level.name
        """Fetch all paid payments for a particular user_id"""
        active_session = (
            db.session.query(Session.id)
            .join(Organization, Session.organization_id == Organization.id)
            .filter(
                Organization.acronym == user.organization.acronym,
                Session.is_active == True
            )
            .scalar()
        )

        query = (
            db.session.query(Payment)
            .join(PaymentItem)
            .join(Department, PaymentItem.department_id == Department.id)
            .join(Level, PaymentItem.level_id == Level.id)
            .join(Organization, Department.organization_id == Organization.id)
            .filter(
                Payment.user_id == user_id,
                Payment.status == 'Paid',
                PaymentItem.academic_session_id == active_session,
                Department.name == user.department.name,
                Level.name == user.level.name,
                Organization.acronym == user.organization.acronym
            )
        )
        return query.all()

# Call the function
# print(fetch_paid_payments(user_id=4))

def fetch_active_session(user_id):
    with app.app_context():
        user = User.query.get(user_id)
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
        return active_session

# Call the function
# print(fetch_active_session(user_id=4))

