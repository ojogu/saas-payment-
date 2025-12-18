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

faculty_routes = Blueprint("faculty", __name__)


@faculty_routes.route("faculty/create", methods=["POST"])
def create_faculty():
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
    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"message": "organization not found"})
    elif organization:
        if Faculty.query.filter_by(
            name=name.upper(), organization_id=organization_id
        ).first():
            return jsonify(
                {"message": f"{name} faculty already exists in {organization.name}"}
            )
        new_faculty = Faculty(
            name=str(name).upper(),
            organization_id=organization_id,
        )
        new_point = ClearancePoint(
            name=str(name).upper(), organization_id=user.get("organization_id")
        )
        db.session.add(new_point)
        db.session.add(new_faculty)
        db.session.commit()
        return jsonify(
            {"message": f"{name} faculty in {organization.name} created successfully"}
        )


@faculty_routes.route("faculty/all", methods=["GET"])
def get_all_faculty():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
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
        return jsonify({"message": "faculty not found"})
    elif organization:
        organization_id = organization.id
        faculty = Faculty.query.filter_by(organization_id=organization_id).all()
        data = []
        for dept in faculty:
            students = User.query.filter_by(faculty_id=dept.id, role="STUDENT").all()
            departments = Department.query.filter_by(faculty_id=dept.id).all()
            dept_data = {
                "id": dept.id,
                "name": str(dept.name).title(),
                "students": len(students),
                "departments": len(departments),
                "dept_list": [department.name for department in departments],
            }
            data.append(dept_data)
        return jsonify(
            {
                "message": f"successfully got all faculties in {organization.name}",
                "data": data,
            }
        )


@faculty_routes.route("/faculty/update/<id>", methods=["PUT"])
def update_faculty(id):
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
    item = Faculty.query.get(id)
    data = request.get_json()
    name = data.get("name")
    item.name = str(name).upper()
    db.session.commit()
    return jsonify({"status": "success", "message": "Faculty Updated"})


@faculty_routes.route("/faculty/<id>", methods=["DELETE"])
def delete_faculty(id):
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
    item = Faculty.query.get(id)
    departments = Department.query.filter_by(faculty_id=id).all()
    for dept in departments:
        code = DepartmentCode.query.filter_by(department_id=dept.id).first()
        if code:
            db.session.delete(code)
        db.session.delete(dept)

    if not item:
        return jsonify({"error": "Faculty not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Faculty deleted successfully"}), 200
