from io import BytesIO

import jwt
from flask import Blueprint, jsonify, request
from openpyxl import load_workbook
from sqlalchemy import or_

#everybody has the same default password except super admin. 
#we have an update password endpoint where users can change their passwords
from src.model import (
    ClearanceItem,
    ClearancePoint,
    Department,
    DepartmentCode,
    MultiClearanceItem,
    Organization,
    PassPorts,
    SchoolSession,
    User,
)
from src.utils.db import db

ALLOWED_EXTENSIONS = {"xlsx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


user_routes = Blueprint("users", __name__)


@user_routes.route("/users/super-admin", methods=["POST"])
def create_super_admin():
    data = request.get_json()
    firstname = data.get("firstname")
    lastname = data.get("lastname")
    email = data.get("email")
    phone = data.get("phone")

    password = "super-admin-default@123"
    role = data.get("role")

    new_user = User(
        firstname=firstname,
        lastname=lastname,
        email=email,
        role=role,
        password_hash=password,
        level=None,
        phone_number=phone,
        organization_id=None,
        clearance_point_id=None,
        department_id=None,
        matric_number=None,
    )
    new_user.set_password(password)
    try:
        if User.query.filter(
            or_(User.email == email, User.phone_number == phone)
        ).first():
            return jsonify({"message": "User may already exist or using this details"})
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": f"{role} Created successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}, 400)


@user_routes.route("/users/create", methods=["POST"])
def create_user():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "SUPERADMIN", "BURSAR", "DATA", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    data = request.get_json()
    firstname = data.get("firstname")
    lastname = data.get("lastname")
    email = data.get("email")
    matric = data.get("matric")
    phone = data.get("phone")
    year = data.get("level")
    password = "admin-default@123"
    role = data.get("role")
    organization_id = user.get("organization_id")
    department_id = data.get("department_id")
    clearance_point_id = data.get("clearance_point_id")

    if role == "ADMIN":
        password = "admin-default@123"
    if role == "SUBADMIN":
        password = "sub-admin-default@123"
    if role == "BURSAR":
        password = "bursar-default@123"
    if role == "DATA":
        password = "data-default@123"

    if role == "AUDIT":
        password = "audit-default@123"

    if user.get("role") == "SUPERADMIN":
        organization_id = data.get("organization")
    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"message": "organization not found"})
    department = None
    level = None
    if department_id:
        if role in ["STUDENT"]:
            department = Department.query.filter_by(
                id=department_id, organization_id=organization.id
            ).first()
            if not department:
                return jsonify(
                    {
                        "message": f"{department.name} does not exist in {organization.name}"
                    }
                )
        if role == "STUDENT":
            level = year
    matric_number = None
    if matric:
        matric_number = matric
    new_user = User(
        firstname=firstname,
        lastname=lastname,
        email=email,
        role=role,
        password_hash=password,
        level=level,
        phone_number=phone,
        organization_id=organization.id,
        clearance_point_id=clearance_point_id,
        department_id=department.id if department else None,
        matric_number=matric_number,
    )
    new_user.set_password(password)
    try:
        if User.query.filter(
            or_(User.email == email, User.phone_number == phone)
        ).first():
            return jsonify({"message": "User may already exist or using this details"})
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": f"{role} Created successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}, 400)


@user_routes.route("/users/create/admin", methods=["POST"])
def create_user_admin():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "SUPERADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    data = request.get_json()
    firstname = data.get("firstname")
    lastname = data.get("lastname")
    email = data.get("email")
    matric = data.get("matric")
    phone = data.get("phone")
    year = data.get("level")
    password = "admin-default@123"
    role = data.get("role")
    organization_id = user.get("organization_id")
    department_id = data.get("department_id")

    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"message": "organization not found"})
    department = None
    level = None
    if department_id:
        if role in ["SUBADMIN", "STUDENT"]:
            department = Department.query.filter_by(
                id=department_id, organization_id=organization.id
            ).first()
            if not department:
                return jsonify(
                    {
                        "message": f"{department.name} does not exist in {organization.name}"
                    }
                )
        if role == "STUDENT":
            level = year
    matric_number = None
    if matric:
        matric_number = matric
    new_user = User(
        firstname=firstname,
        lastname=lastname,
        email=email,
        role=role,
        password_hash=password,
        level=level,
        phone_number=phone,
        organization_id=organization.id,
        department_id=department.id if department else None,
        matric_number=matric_number,
        faculty_id=None,
    )
    new_user.set_password(password)
    try:
        if User.query.filter(
            or_(User.email == email, User.phone_number == phone)
        ).first():
            return jsonify({"message": "User may already exist or using this details"})
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": f"{role} Created successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}, 400)


@user_routes.route("users/<role>", methods=["GET"])
def get_users_by_role(role):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "SUPERADMIN", "BURSAR", "DATA", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    if user.get("role") == "SUPERADMIN":
        users = User.query.filter_by(role=role).all()
    else:
        organization = Organization.query.filter_by(
            id=user.get("organization_id")
        ).first()
        if not organization:
            return jsonify({"message": "Organization not found"})

        users = User.query.filter_by(organization_id=organization.id, role=role).all()

    data = []
    for user in users:
        department = Department.query.filter_by(id=user.department_id).first()
        clearance_point = ClearancePoint.query.filter_by(
            id=user.clearance_point_id
        ).first()
        if department:
            org_data = {
                "id": user.id,
                "last_name": user.lastname,
                "first_name": user.firstname,
                "middle": user.middlename,
                "department": str(department.name).title(),
                "email": user.email,
                "organization": organization.name,
                "matric_number": user.matric_number,
                "level": user.level,
                "faculty": str(department.faculty.name).title(),
            }
        elif clearance_point:
            org_data = {
                "id": user.id,
                "name": user.firstname + " " + user.lastname,
                "first_name": user.firstname,
                "last_name": user.lastname,
                "department": "-",
                "office": str(user.clearance_point.name).title(),
                "clearance_point_id": user.clearance_point_id,
                "email": user.email,
                "phone": user.phone_number,
                "organization": organization.name,
            }
        elif not user.organization:
            org_data = {
                "id": user.id,
                "name": user.firstname + " " + user.lastname,
                "first_name": user.firstname,
                "last_name": user.lastname,
                "email": user.email,
                "phone": user.phone_number,
                "matric": user.matric_number,
                "level": user.level,
            }
        else:
            org_data = {
                "id": user.id,
                "name": user.firstname + " " + user.lastname,
                "first_name": user.firstname,
                "last_name": user.lastname,
                "department": "-",
                "office": str(user.clearance_point.name).title()
                if user.clearance_point_id != None
                else None,
                "email": user.email,
                "phone": user.phone_number,
                "organization": user.organization.name,
                "organization_id": user.organization.id,
                "matric": user.matric_number,
                "level": user.level,
            }
        data.append(org_data)
    return jsonify({"message": "successfully got all users", "data": data})


@user_routes.route("users/point", methods=["POST"])
def get_users_by_point():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "SUPERADMIN", "BURSAR", "SUBADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401

    if user.get("role") == "SUBADMIN":
        users = User.query.filter_by(
            clearance_point_id=user.get("clearance_point_id")
        ).all()
    data = request.get_json()
    clearance_point_id = data.get("point_id")
    if not clearance_point_id and user.get("role") != "SUBADMIN":
        return jsonify(
            {"status": "success", "message": "successfully got all users", "data": []}
        )
    users = User.query.filter_by(clearance_point_id=clearance_point_id).all()
    if user.get("role") == "SUBADMIN":
        users = User.query.filter_by(
            clearance_point_id=user.get("clearance_point_id")
        ).all()
    data = []
    for user in users:
        org_data = {
            "id": user.id,
            "name": user.firstname + " " + user.lastname,
            "first_name": user.firstname,
            "last_name": user.lastname,
            "department": "-",
            "office": str(user.clearance_point.name).title(),
            "clearance_point_id": user.clearance_point_id,
            "email": user.email,
            "phone": user.phone_number,
        }

        data.append(org_data)

    return jsonify(
        {"status": "success", "message": "successfully got all users", "data": data}
    )


@user_routes.route("users/STUDENT/<page>", methods=["GET"])
def get_all_students(page):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "DATA", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization not found"})

    users = (
        User.query.filter_by(organization_id=organization.id, role="STUDENT")
        .offset((int(page) - 1) * 10)
        .limit(10)
        .all()
    )
    data = []
    for user in users:
        department = Department.query.filter_by(id=user.department_id).first()
        clearance_point = ClearancePoint.query.filter_by(
            id=user.clearance_point_id
        ).first()
        if department:
            passport = PassPorts.query.filter_by(student_id=user.id).first()
            org_data = {
                "id": user.id,
                "last_name": user.lastname,
                "first_name": user.firstname,
                "middle": user.middlename,
                "department": str(department.name).title(),
                "department_id": user.department_id,
                "email": user.email,
                "organization": organization.name,
                "matric_number": user.matric_number,
                "level": user.level,
                "faculty": str(department.faculty.name).title(),
                "passport": "https://myclearance.qplusgnl.com/uploads/"
                + passport.file_url
                if passport
                else None,
            }
        elif clearance_point:
            org_data = {
                "id": user.id,
                "name": user.firstname + " " + user.lastname,
                "department": "-",
                "office": str(user.clearance_point.name).title(),
                "email": user.email,
                "organization": organization.name,
                "matric": user.matric_number,
                "level": user.level,
            }
        else:
            org_data = {
                "id": user.id,
                "name": user.firstname + " " + user.lastname,
                "department": "-",
                "office": user.clearance_point.name
                if user.clearance_point_id != None
                else None,
                "email": user.email,
                "organization": organization.name,
                "matric": user.matric_number,
                "level": user.level,
            }
        data.append(org_data)
    return jsonify({"message": "successfully got all users", "data": data})


@user_routes.route("users/students", methods=["GET"])
def get_total_students():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "DATA", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization not found"})

    users = User.query.filter_by(organization_id=organization.id, role="STUDENT").all()
    return jsonify({"message": "success", "total": len(users)})


@user_routes.route("users/<faculty_id>/<role>", methods=["GET"])
def get_users_by_faculty(faculty_id, role):
    try:
        SECRET_KEY = "balablu-01101"

        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "DATA", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization not found"})
    users = User.query.filter_by(
        organization_id=organization.id, role=role, faculty_id=faculty_id
    ).all()
    data = []
    for user in users:
        department = Department.query.filter_by(id=user.department_id).first()
        if department:
            passport = PassPorts.query.filter_by(student_id=user.id).first()
            org_data = {
                "id": user.id,
                "last_name": user.lastname,
                "first_name": user.firstname,
                "middle": user.middlename,
                "department": str(department.name).title(),
                "department_id": user.department_id,
                "email": user.email,
                "organization": organization.name,
                "matric_number": user.matric_number,
                "level": user.level,
                "faculty": str(department.faculty.name).title(),
                "passport": "https://myclearance.qplusgnl.com/uploads/"
                + passport.file_url
                if passport
                else None,
            }
        else:
            org_data = {
                "id": user.id,
                "name": user.firstname + " " + user.lastname,
                "department": "Random",
                "email": user.email,
                "organization": organization.name,
                "matric": user.matric_number,
                "level": user.level,
            }
        data.append(org_data)
    return jsonify({"message": "successfully got all users", "data": data})


@user_routes.route("users/department/<dept_id>/<role>", methods=["GET"])
def get_users_by_dept(dept_id, role):
    try:
        SECRET_KEY = "balablu-01101"

        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "DATA", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization not found"})
    users = User.query.filter_by(
        organization_id=organization.id, role=role, department_id=dept_id
    ).all()
    data = []
    for user in users:
        department = Department.query.filter_by(id=user.department_id).first()
        if department:
            passport = PassPorts.query.filter_by(student_id=user.id).first()
            org_data = {
                "id": user.id,
                "last_name": user.lastname,
                "first_name": user.firstname,
                "middle": user.middlename,
                "department": str(department.name).title(),
                "department_id": user.department_id,
                "email": user.email,
                "organization": organization.name,
                "matric_number": user.matric_number,
                "level": user.level,
                "faculty": str(department.faculty.name).title(),
                "passport": "https://myclearance.qplusgnl.com/uploads/"
                + passport.file_url
                if passport
                else None,
            }
        else:
            org_data = {
                "id": user.id,
                "name": user.firstname + " " + user.lastname,
                "department": "Random",
                "email": user.email,
                "organization": organization.name,
                "matric": user.matric_number,
                "level": user.level,
            }
        data.append(org_data)
    return jsonify({"message": "successfully got all users", "data": data})


@user_routes.route("users/student/<path:matric>", methods=["GET"])
def get_student(matric):
    try:
        SECRET_KEY = "balablu-01101"

        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "SUBADMIN", "BURSAR", "DATA", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization not found"})
    users = User.query.filter_by(
        organization_id=organization.id, role="STUDENT", matric_number=matric
    ).all()
    data = []
    for user in users:
        department = Department.query.filter_by(id=user.department_id).first()
        if department:
            passport = PassPorts.query.filter_by(student_id=user.id).first()
            org_data = {
                "id": user.id,
                "last_name": user.lastname,
                "first_name": user.firstname,
                "middle": user.middlename,
                "department": str(department.name).title(),
                "department_id": user.department_id,
                "email": user.email,
                "organization": organization.name,
                "matric_number": user.matric_number,
                "level": user.level,
                "faculty": str(department.faculty.name).title(),
                "passport": "https://myclearance.qplusgnl.com/uploads/"
                + passport.file_url
                if passport
                else None,
            }
        else:
            org_data = {
                "id": user.id,
                "name": user.firstname + " " + user.lastname,
                "department": "Random",
                "email": user.email,
                "organization": organization.name,
                "matric": user.matric_number,
                "level": user.level,
            }
        data.append(org_data)
    return jsonify({"message": "successfully got all users", "data": data})


@user_routes.route("users/student/filter/<path:name>", methods=["GET"])
def filter_student(name):
    try:
        SECRET_KEY = "balablu-01101"

        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "SUBADMIN", "BURSAR", "DATA", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization not found"})
    users = User.query.filter(
        User.organization_id == organization.id,
        User.role == "STUDENT",
        User.lastname == str(name).upper(),
    ).all()
    data = []
    for user in users:
        department = Department.query.filter_by(id=user.department_id).first()
        if department:
            passport = PassPorts.query.filter_by(student_id=user.id).first()
            org_data = {
                "id": user.id,
                "last_name": user.lastname,
                "first_name": user.firstname,
                "middle": user.middlename,
                "department": str(department.name).title(),
                "department_id": user.department_id,
                "email": user.email,
                "organization": organization.name,
                "matric_number": user.matric_number,
                "level": user.level,
                "faculty": str(department.faculty.name).title(),
                "passport": "https://myclearance.qplusgnl.com/uploads/"
                + passport.file_url
                if passport
                else None,
            }
        else:
            org_data = {
                "id": user.id,
                "name": user.firstname + " " + user.lastname,
                "department": "Random",
                "email": user.email,
                "organization": organization.name,
                "matric": user.matric_number,
                "level": user.level,
            }
        data.append(org_data)
    return jsonify({"message": "successfully got all users", "data": data})


@user_routes.route("users/<role>/update", methods=["PUT"])
def update_users(role):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        admin = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if admin.get("role") not in ["ADMIN", "SUPERADMIN", "BURSAR", "DATA"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    data = request.get_json()
    id = data.get("id")
    firstname = data.get("firstname")
    lastname = data.get("lastname")
    middlename = data.get("middlename")
    email = data.get("email")
    phone_number = data.get("phone")
    matric = data.get("matric")
    level = data.get("level")
    department_id = data.get("department_id")
    clearance_point_id = data.get("clearance_point_id")
    passport = data.get("passport")

    if role == "STUDENT":
        user = User.query.filter_by(id=id).first()
        pass_image = PassPorts.query.filter_by(student_id=user.id).first()
        department = Department.query.filter_by(id=department_id).first()
        user.firstname = firstname
        user.middlename = middlename
        user.lastname = lastname
        user.email = email
        user.level = level
        if department:
            user.department_id = department_id
        if matric != "":
            user.matric_number = matric
        user.faculty_id = department.faculty_id
        if passport != None and pass_image == None:
            new_passport = PassPorts(
                student_id=user.id,
                file_url=passport,
            )
            db.session.add(new_passport)
            db.session.commit()
        elif pass_image != None and passport != None:
            pass_image.file_url = passport

    if role == "SUBADMIN":
        if clearance_point_id == "" or clearance_point_id == None:
            return jsonify({"message": "Clearance Office is compulsory"})
        user = User.query.filter_by(id=id).first()
        user.firstname = firstname
        user.lastname = lastname
        user.email = email
        user.phone_number = phone_number
        user.clearance_point_id = clearance_point_id
    if role in ["ADMIN", "BURSAR", "DATA", "AUDIT"]:
        user = User.query.filter_by(id=id).first()
        user.firstname = firstname
        user.lastname = lastname
        user.email = email
        user.phone_number = phone_number
        if admin.get("role") == "SUPERADMIN":
            user.organization_id = data.get("organization_id")
    if role in ["SUPERADMIN"]:
        user = User.query.filter_by(id=id).first()
        user.firstname = firstname
        user.lastname = lastname
        user.email = email
        user.phone_number = phone_number
    # user.set_password('default@123')
    db.session.commit()
    return jsonify({"message": "Successfully Updated"})


@user_routes.route("subadmin/<role>/<page>", methods=["GET"])
def get_users_by_subadmin(role, page):
    try:
        SECRET_KEY = "balablu-01101"

        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["SUBADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    details = User.query.get(user.get("id"))
    organization_id = user.get("organization_id")
    clearance_point = ClearancePoint.query.filter_by(
        id=details.clearance_point_id
    ).first()
    if not clearance_point:
        return jsonify({"message": "Department not found"})
    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"message": "Organization not found"})
    clearance_items = ClearanceItem.query.filter_by(
        clearance_point_id=clearance_point.id
    ).all()
    data = []
    total_users = []
    total = 0
    for item in clearance_items:
        if item.is_global == True:
            users = (
                User.query.filter_by(organization_id=organization.id, role=role)
                .offset((int(page) - 1) * 10)
                .limit(10)
                .all()
            )
            total_users = User.query.filter_by(
                organization_id=organization.id, role=role
            ).all()
            total = len(total_users)
            for user in users:
                org_data = {
                    "id": user.id,
                    "name": user.firstname + " " + user.lastname,
                    "first_name": user.firstname,
                    "last_name": user.lastname,
                    "middle_name": user.middlename,
                    "level": user.level,
                    "department": user.department.name,
                    "role": user.role,
                    "matric": user.matric_number,
                    "organization": organization.name,
                }
                if org_data not in data:
                    data.append(org_data)
            break
        else:
            multi = MultiClearanceItem.query.filter_by(clearance_item_id=item.id).all()
            for mul in multi:
                users = (
                    User.query.filter_by(
                        department_id=mul.department_id,
                        organization_id=organization.id,
                        role=role,
                    )
                    .offset((int(page) - 1) * 10)
                    .limit(10)
                    .all()
                )
                total_users = User.query.filter_by(
                    department_id=mul.department_id,
                    organization_id=organization.id,
                    role=role,
                ).all()
                total += len(total_users)
                for user in users:
                    org_data = {
                        "id": user.id,
                        "name": user.firstname + " " + user.lastname,
                        "first_name": user.firstname,
                        "last_name": user.lastname,
                        "middle_name": user.middlename,
                        "level": user.level,
                        "department": user.department.name,
                        "role": user.role,
                        "matric": user.matric_number,
                        "organization": organization.name,
                    }
                    if org_data not in data:
                        data.append(org_data)
    return jsonify(
        {
            "message": f"successfully got all {role} in {clearance_point.name} department of {organization.name}",
            "data": data,
            "total": total,
        }
    )


@user_routes.route("/users/get", methods=["POST"])
def get_user():
    data = request.get_json()
    get_with = data.get("get_with")
    query = data.get("query")
    if get_with == "email":
        user = User.query.filter_by(email=query).first()
    elif get_with == "matric_number":
        user = User.query.filter_by(matric_number=query).first()
    if user.department_id:
        dept = Department.query.filter_by(id=user.department_id).first()
    if user.organization_id:
        org = Organization.query.filter_by(id=user.organization_id).first()
    user_data = {
        "firstname": user.firstname,
        "lastname": user.lastname,
        "email": user.email,
        "phone": user.phone_number,
        "role": user.role,
        "department": dept.name if dept else None,
        "organization": org.name if org else None,
    }
    return jsonify(
        {"message": f"successfully found {user.role} user", "data": user_data}
    )


@user_routes.route("/students/bulk-upload", methods=["POST"])
def bulk_upload_users():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400

    organization_id = user.get("organization_id")
    last_session = SchoolSession.query.order_by(SchoolSession.id.desc()).first()
    if not last_session:
        return jsonify({"message": "No session"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify(
            {"message": "Invalid file type. Only Excel (.xlsx) files are allowed."}
        ), 400

    # Load the Excel file
    try:
        file.stream.seek(0)
        workbook = load_workbook(filename=BytesIO(file.read()))
        sheet = workbook.active  # Get the first sheet
    except Exception as e:
        return jsonify({"message": f"Failed to read Excel file: {str(e)}"}), 400

    users = []
    existing_users = []
    matrics = []
    skipped = []

    # Iterate through rows, assuming the first row contains headers
    for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip the header row
        firstname, lastname, middlename, matric, email, phone, level, dept = row[:8]

        # Validate required fields
        if not matric:
            continue

        organization = Organization.query.filter_by(id=organization_id).first()
        if not organization:
            return jsonify({"message": "organization not found"})
        try:
            code = matric.split("/")
            dept_code = DepartmentCode.query.filter_by(
                code=str(code[1]).upper()
            ).first()
            if str(code[1]).upper() == "D":
                dept_code = DepartmentCode.query.filter_by(
                    code=str(code[2]).upper()
                ).first()
            if not dept_code:
                skipped.append(matric)
                print("department")
                continue
            department = Department.query.get(dept_code.department_id)
            existing_user = User.query.filter(or_(User.matric_number == matric)).first()

            if existing_user:
                existing_users.append(email)
                skipped.append(matric)
                continue
            if matric in matrics:
                skipped.append(matric)
                continue
            year = 2000 + int(code[0])
            current_year = SchoolSession.query.filter_by(
                is_active=True, organization_id=organization_id
            ).first()
            years = current_year.end_year - year
            level = years * 100
            user = User(
                firstname=firstname,
                lastname=lastname,
                middlename=middlename,
                email=email,
                role="STUDENT",
                password_hash="default@123",
                phone_number=phone,
                level=level,
                organization_id=organization.id,
                department_id=department.id,
                matric_number=matric,
                faculty_id=department.faculty_id,
            )
            user.set_password("default@123")
            users.append(user)
            matrics.append(matric)
            print("success")
        except Exception as err:
            print(err)
            skipped.append(matric)
            continue

    # Bulk insert for new users
    db.session.bulk_save_objects(users)
    db.session.commit()

    return jsonify(
        {
            "message": f"{len(users)} users uploaded successfully.",
            "existing": len(skipped),
        }
    ), 201


@user_routes.route("users/<role>/<email>", methods=["DELETE"])
def delete_user(email, role):
    # try:
    #     SECRET_KEY="balablu-01101"
    #     print(request.headers.get('Authorization'))
    #     decoded=jwt.decode(request.headers.get('Authorization'),SECRET_KEY,algorithms=["HS256"])
    #     user=decoded
    # except Exception as e:
    #    return jsonify({"message":f"Invalid auth token"})
    # if user.get('role') not in ['ADMIN','SUPERADMIN','DATA']:
    #     return jsonify({'message':"Unauthorized Access"}),401
    items = User.query.filter_by(email=email, role=role).all()
    for item in items:
        if not item:
            return jsonify({"error": "User not found"}), 404

        db.session.delete(item)
        db.session.commit()

    return jsonify({"message": "User deleted successfully"}), 200
