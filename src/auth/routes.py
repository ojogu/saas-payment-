from flask_jwt_extended import create_access_token
import jwt
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from src.auth.schema import Login
from src.service.user_service import UserService
from src.utils.db import db
auth_bp = Blueprint("auth", __name__)


def generate_token(email, user, change_pass):
    SECRET_KEY = "balablu-01101"
    claims = {
        "sub": email,
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "level": user.level,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "matric_number": user.matric_number,
        "organization_id": user.organization_id,
        "department_id": user.department_id,
        "clearance_point_id": user.clearance_point_id,
        "change_pass": change_pass,
    }
    return jwt.encode(claims, SECRET_KEY)


def fix_padding(string):
    return string + "=" * ((4 - len(string) % 4) % 4)


def generated_padded_token(token):
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid jwt structure")
    header = fix_padding(parts[0])
    payloaf = fix_padding(parts[1])
    signature = fix_padding(parts[2])

    padded_token = ".".join([header, payloaf, signature])

    return padded_token


@auth_bp.route("/login", methods=["POST"])
def login():
    data:dict = request.get_json()
    validated_data = Login(**data)
    # credential = data.get("credential")
    # password = data.get("password")
    
    #move to service class 
    user_service = UserService(db)
    
    jwt_payload:dict = user_service.authenticate_user(validated_data)
    access_token = create_access_token(
        identity=jwt_payload.get("user_id"),
        additional_claims=jwt_payload.get("role")
        
        )
    stmt = db.execute(
            select(User).where(
                User.email == credential
            )
    )
    user = stmt.scalar_or_first()
    if not user:
        user = User.query.filter_by(matric_number=credential).first()
        if not user:
            return jsonify({"message": "User not found"})
    if not user.check_password(password):
        return jsonify({"message": "Invalid Password"})
    change_pass = True
    if password == "default@123":
        token = generate_token(credential, user, True)

    else:
        token = generate_token(credential, user, False)
        change_pass = False

    if user.role == "SUPERADMIN":
        return jsonify(
            {
                "token": token,
                "res_name": user.firstname + " " + user.lastname,
                "role": user.role,
                "change_pass": change_pass,
            }
        )
    department = Department.query.get(user.department_id)
    organization = Organization.query.get(user.organization_id)
    current_session = Session.query.filter_by(
        is_active=True, organization_id=organization.id
    ).first()
    if department:
        passport = PassPorts.query.filter_by(student_id=user.id).first()
        return jsonify(
            {
                "token": token,
                "res_name": str(user.firstname)
                + " "
                + str(user.middlename)
                + " "
                + str(user.lastname),
                "department": department.name,
                "organization": organization.name,
                "level": user.level,
                "matric": user.matric_number,
                "session": current_session.id,
                "role": user.role,
                "change_pass": change_pass,
                "organization_id": organization.id,
                "passport": "https://myclearance.qplusgnl.com/uploads/"
                + passport.file_url
                if passport
                else None,
            }
        )
    elif organization and not department:
        return jsonify(
            {
                "token": token,
                "res_name": user.firstname + " " + user.lastname,
                "department": organization.name,
                "organization_id": organization.id,
                "role": user.role,
                "session": current_session.id if current_session else None,
                "change_pass": change_pass,
            }
        )


@auth_bp.route("/student/login", methods=["POST"])
def student_login():
    data = request.get_json()
    matric = data.get("matric")
    password = data.get("password")
    user = User.query.filter_by(matric_number=matric).first()
    if not user:
        return jsonify({"message": "User not found"})
    if not user.check_password(password):
        return jsonify({"message": "Invalid Password"})

    token = generate_token(matric, user)
    department = Department.query.get(user.department_id)
    organization = Organization.query.get(user.organization_id)
    current_session = Session.query.order_by(Session.id.desc()).first()
    if department:
        return jsonify(
            {
                "token": token,
                "res_name": user.firstname
                + " "
                + user.lastname
                + " "
                + user.middlename,
                "department": department.name,
                "organization": organization.name,
                "level": user.level,
                "matric": user.matric_number,
                "session": current_session.name,
            }
        )
    else:
        return jsonify(
            {
                "token": token,
                "res_name": user.firstname + " " + user.lastname,
                "department": organization.name,
            }
        )


@auth_bp.route("/update")
def bulk_update_passwords():
    users = db.session.query(User).all()  # Fetch all users from your database
    for user in users:
        if user.password_hash:
            try:
                # Generate new hash
                new_hash = generate_password_hash(
                    "default@123", method="pbkdf2:sha256", salt_length=12
                )
                # Update in the database
                update_user_password_in_db(user, new_hash)
                print(f"Updated password for user: {user.id}")
            except Exception as e:
                print(f"Failed to update password for user: {user.id} - {e}")


@auth_bp.route("/update/password", methods=["POST"])
def update_password():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "SUBADMIN", "STUDENT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    id = user.get("id")
    user = User.query.get(id)
    data = request.get_json()
    new = data.get("new")
    if user.password_hash:
        try:
            new_hash = generate_password_hash(
                new, method="pbkdf2:sha256", salt_length=12
            )
            update_user_password_in_db(user, new_hash)
            return jsonify({"message": f"Updated password for user: {user.id}"})
        except Exception:
            return jsonify(
                {"message": f"Failed to update password for user: {user.id}"}
            )


def update_user_password_in_db(user, new_hash):
    user.password_hash = new_hash
    db.session.commit()
