from datetime import datetime

import jwt
from flask import Blueprint, jsonify, request
from sqlalchemy import func

from src.model import ClearanceLogs, Organization
from src.utils.db import db

clearance_log = Blueprint("clearance_log", __name__)


@clearance_log.route("/clearance_logs/all", methods=["GET"])
def get_all_log():
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
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization not found"})
    data = []
    query = db.session.query(ClearanceLogs)
    query = query.filter(ClearanceLogs.organization_id == organization.id)
    today = datetime.today().date()
    query = query.filter(func.date(ClearanceLogs.created_at) == today)
    logs = query.order_by(ClearanceLogs.created_at.desc()).all()
    for log in logs:
        log_data = {
            "id": log.id,
            "action": log.action,
            "email": log.email,
            "matric": log.matric,
            "role": log.role,
            "time": log.created_at,
        }
        data.append(log_data)
    return jsonify({"message": "successfully got all logs", "data": data})
