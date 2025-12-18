import jwt
from flask import Blueprint, jsonify, request

from src.model import (
    ClearanceItem,
    ClearancePoint,
    Department,
    MultiClearanceItem,
    Organization,
    db,
)

clearance_point = Blueprint("clearance_point", __name__)


@clearance_point.route("/clearance_point/create", methods=["POST"])
def create_point():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    data = request.get_json()
    name = data.get("name")
    if name:
        new_point = ClearancePoint(
            name=str(name).upper(), organization_id=user.get("organization_id")
        )
        db.session.add(new_point)
        db.session.commit()
        return jsonify(
            {"status": "success", "message": "Clearing Department Created Successfully"}
        )
    else:
        return jsonify({"message": "Name is required"})


@clearance_point.route("/clearance_points/all", methods=["GET"])
def get_all():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "SUBADMIN", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization not found"})
    elif organization:
        organization_id = organization.id
        all_departments = Department.query.filter_by(
            organization_id=organization_id
        ).all()
        clearance_points = ClearancePoint.query.filter_by(
            organization_id=organization_id
        ).all()
        data = []

        for point in clearance_points:
            clearance_items = ClearanceItem.query.filter_by(
                clearance_point_id=point.id
            ).all()
            departments = []
            for item in clearance_items:
                if item.is_global == True:
                    for department in all_departments:
                        if department.name not in departments:
                            departments.append(department.name)
                multi = MultiClearanceItem.query.filter_by(
                    clearance_item_id=item.id
                ).all()
                for mul in multi:
                    if mul.department.name not in departments:
                        departments.append(mul.department.name)
            point_data = {
                "id": point.id,
                "name": str(point.name).title(),
                "clearance_items": len(clearance_items),
                "departments": len(departments),
            }
            data.append(point_data)
        data = sorted(data, key=lambda x: x["name"])
        return jsonify({"status": "success", "data": data})


@clearance_point.route("/clearance_point/update/<id>", methods=["PUT"])
def update_clearance_point(id):
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    item = ClearancePoint.query.get(id)
    data = request.get_json()
    name = data.get("name")
    item.name = str(name).upper()
    db.session.commit()
    return jsonify({"status": "success", "message": "Clearance Updated"})


@clearance_point.route("/clearance_point/<id>", methods=["DELETE"])
def delete_point(id):
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    item = ClearancePoint.query.get(id)

    if not item:
        return jsonify({"error": "Clearance Point not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Clearance Point deleted successfully"}), 200
