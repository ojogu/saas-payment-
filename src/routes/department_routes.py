import jwt
from flask import Blueprint, jsonify, request

from src.model import (
    ClearancePoint,
    Department,
    DepartmentCode,
    Faculty,
    Organization,
    User,
    db,
)

department_routes = Blueprint("department", __name__)


@department_routes.route("departments/create", methods=["POST"])
def create_department():
    data = request.get_json()
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    name = data.get("name")
    organization_id = user.get("organization_id")
    faculty_id = data.get("faculty_id")
    code = data.get("code")
    organization = Organization.query.filter_by(id=organization_id).first()
    faculty = Faculty.query.filter_by(id=faculty_id).first()
    if not organization:
        return jsonify({"message": "organization not found"})
    if not faculty:
        return jsonify({"message": "faculty not found"})
    existing_code = DepartmentCode.query.filter_by(
        code=code, organization_id=organization_id
    ).first()
    if existing_code:
        return jsonify({"message": "code already exists"})
    elif code == "":
        return jsonify({"message": "Code cannot be empty"})
    elif organization:
        if Department.query.filter_by(
            name=name.upper(), organization_id=organization_id
        ).first():
            return jsonify(
                {"message": f"{name} department already exists in {organization.name}"}
            )

        new_department = Department(
            name=str(name).upper(),
            organization_id=organization_id,
            faculty_id=faculty_id,
        )
        new_point = ClearancePoint(
            name=str(name).upper(), organization_id=user.get("organization_id")
        )

        db.session.add(new_department)
        db.session.add(new_point)
        db.session.commit()
        new_code = DepartmentCode(
            code=str(code).upper(),
            organization_id=organization_id,
            department_id=new_department.id,
        )
        db.session.add(new_code)
        db.session.commit()

        return jsonify(
            {
                "message": f"{name} department in {organization.name} created successfully"
            }
        )


@department_routes.route("departments/all", methods=["GET"])
def get_all_departments():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "SUBADMIN", "DATA", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "organization not found"})
    elif organization:
        organization_id = organization.id
        departments = Department.query.filter_by(organization_id=organization_id).all()

        data = []
        for dept in departments:
            students = User.query.filter_by(department_id=dept.id, role="STUDENT").all()
            code = DepartmentCode.query.filter_by(department_id=dept.id).first()
            dept_data = {
                "id": dept.id,
                "name": str(dept.name).title(),
                "faculty_id": dept.faculty_id,
                "faculty": str(dept.faculty.name).title() if dept.faculty else None,
                "students": len(students),
                "code": code.code if code else "-",
            }
            data.append(dept_data)
        data = sorted(data, key=lambda x: x["name"])
        # if user.get('role') == 'SUBADMIN':
        #     data = []
        return jsonify(
            {
                "message": f"successfully got all departments in {organization.name}",
                "data": data,
            }
        )


@department_routes.route("/department/update/<id>", methods=["PUT"])
def update_department(id):
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
    item = Department.query.get(id)
    data = request.get_json()
    name = data.get("name")
    code = data.get("code")
    item.name = str(name).upper()
    item.faculty_id = data.get("faculty_id")
    existing_code = DepartmentCode.query.filter_by(department_id=id).first()
    if existing_code:
        print(code)
        existing_code.code = code
        db.session.commit()
    elif code == "":
        return jsonify({"message": "code cannot be empty"})
    else:
        new_code = DepartmentCode(
            code=str(code).upper(),
            organization_id=user.get("organization_id"),
            department_id=id,
        )
        db.session.add(new_code)
    db.session.commit()
    return jsonify({"status": "success", "message": "Department Updated"})


@department_routes.route("/department/<id>", methods=["DELETE"])
def delete_department(id):
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
    item = Department.query.get(id)

    if not item:
        return jsonify({"error": "Department not found"}), 404
    existing_code = DepartmentCode.query.filter_by(department_id=id).first()
    db.session.delete(item)
    if existing_code:
        db.session.delete(existing_code)
    db.session.commit()

    return jsonify({"message": "Department deleted successfully"}), 200
