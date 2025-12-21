import jwt
from flask import Blueprint, jsonify, request

from src.model import Organization, SchoolSession, User
from src.utils.db import db

session_route = Blueprint("session", __name__)


@session_route.route("/session/create", methods=["POST"])
def create_session():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "organization not found"})
    data = request.get_json()
    name = data.get("name")
    start_year = data.get("start_year")
    end_year = data.get("end_year")
    is_active = data.get("is_active")
    current = data.get("old_session")
    existing_session = SchoolSession.query.filter_by(
        start_year=start_year, organization_id=organization.id
    ).first()
    existing_session_name = SchoolSession.query.filter_by(
        name=name, organization_id=organization.id
    ).first()
    existing_session_end = SchoolSession.query.filter_by(
        end_year=end_year, organization_id=organization.id
    ).first()
    if existing_session or existing_session_name or existing_session_end:
        return jsonify({"message": "session already exists"})
    if (int(end_year) - int(start_year)) > 1 or (int(end_year) - int(start_year)) < 1:
        return jsonify({"message": "Invalid year must be 1 year apart"})
    if is_active == True:
        current_session = SchoolSession.query.get(current)
        if current_session:
            current_session.is_active = False
            students = User.query.filter_by(
                role="STUDENT", organization_id=organization.id
            ).all()
            for student in students:
                if student.level < 600:
                    level = int(student.level)
                    level += 100
                    student.level = level
    new_session = SchoolSession(
        name=name,
        start_year=start_year,
        end_year=end_year,
        is_active=is_active,
        organization_id=organization.id,
    )
    db.session.add(new_session)
    db.session.commit()

    return jsonify({"message": "SchoolSession Created Successfully"})


@session_route.route("/session/update", methods=["PUT"])
def update_session():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    data = request.get_json()
    id = data.get("id")
    name = data.get("name")
    start_year = data.get("start_year")
    end_year = data.get("end_year")
    is_active = data.get("is_active")
    current = SchoolSession.query.filter_by(
        is_active=True, organization_id=user.get("organization_id")
    ).first()
    session = SchoolSession.query.get(id)
    existing_session = SchoolSession.query.filter_by(start_year=start_year).first()
    existing_session_name = SchoolSession.query.filter_by(name=name).first()
    existing_session_end = SchoolSession.query.filter_by(end_year=end_year).first()
    check = session.query.filter_by(
        start_year=start_year, end_year=end_year, name=name
    ).first()
    # if check:
    #     return jsonify({'message':'session already exists'})
    if (int(end_year) - int(start_year)) > 1 or (int(end_year) - int(start_year)) < 1:
        return jsonify({"message": "Invalid year must be 1 year apart"})

    session.name = name
    session.start_year = start_year
    session.end_year = end_year
    if is_active == True and current and current.id != session.id:
        current.is_active = False
    session.is_active = is_active
    db.session.commit()

    return jsonify({"message": "SchoolSession Updated Successfully"})


@session_route.route("/session/create/open", methods=["POST"])
def create_open_session():
    data = request.get_json()
    name = data.get("name")
    # students=User.query.filter_by(role="STUDENT").all()
    # for student in students:
    #     level=int(student.level)
    #     level+=100
    #     student.level=level
    new_session = SchoolSession(name=name)
    db.session.add(new_session)
    db.session.commit()

    return jsonify({"message": "SchoolSession Created Successfully"})


@session_route.route("/session/all", methods=["GET"])
def get_sessions():
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
    sessions = SchoolSession.query.filter_by(
        organization_id=user.get("organization_id")
    ).all()
    data = []
    for session in sessions:
        sess_data = {
            "id": session.id,
            "name": session.name,
            "is_active": session.is_active,
            "start_year": session.start_year,
            "end_year": session.end_year,
        }
        data.append(sess_data)

    return jsonify({"message": "success", "data": data})


@session_route.route("/session/<id>", methods=["GET"])
def get_session(id):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "DATA"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    session = SchoolSession.query.get(id)
    data = []
    if session:
        sess_data = {
            "id": session.id,
            "name": session.name,
            "start_year": session.start_year,
            "end_year": session.end_year,
        }
    else:
        sess_data = {
            "id": None,
            "name": None,
            "start_year": None,
            "end_year": None,
        }

    return jsonify({"message": "success", "data": sess_data})


@session_route.route("/session/delete", methods=["POST"])
def delete_sessions():
    sessions = SchoolSession.query.all()
    for session in sessions:
        if not session:
            return jsonify({"message": "SchoolSession not found"}), 404

        db.session.delete(session)

    new_session = SchoolSession(name="2024/2025 SchoolSession")
    db.session.add(new_session)
    db.session.commit()
    return jsonify({"message": "Sessions deleted successfully and updated"}), 200


@session_route.route("/session/delete/<id>", methods=["DELETE"])
def delete_session(id):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    session = SchoolSession.query.get(id)
    if not session:
        return jsonify({"message": "SchoolSession not found"}), 404

    db.session.delete(session)
    db.session.commit()
    return jsonify(
        {"status": "success", "message": "SchoolSession deleted successfully"}
    ), 200
