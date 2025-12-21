from datetime import datetime, timedelta

import jwt
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from src.utils.db import db
from src.model import (
    Clearance,
    ClearanceItem,
    Department,
    Organization,
    PassPorts,
    Payment,
    User,
)

bursar_route = Blueprint("bursar", __name__)


@bursar_route.route("/payments/all", methods=["POST"])
def get_all_payments():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["BURSAR", "ADMIN", "SUBADMIN", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    # clearance_items=ClearanceItem.query.filter_by(organization_id=user.get('organization_id'),payment_required=True)
    data = request.get_json()
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "organization not found"})
    details = User.query.get(user.get("id"))
    payments = []
    total = 0
    query = db.session.query(Payment).join(User).join(Clearance).join(ClearanceItem)
    query = query.filter(User.organization_id == organization.id)
    all = query.all()
    for payment in all:
        if payment.system_payment == True:
            total += 10000
        else:
            total += payment.amount

    if user.get("role") in ["BURSAR", "ADMIN", "AUDIT"]:
        length = len(query.all())
    if user.get("role") in ["SUBADMIN"]:
        query = db.session.query(Payment).join(User).join(Clearance).join(ClearanceItem)
        query = query.filter(
            ClearanceItem.clearance_point_id == details.clearance_point_id
        )
        length = len(query.all())
    if data.get("department"):
        query = query.filter(User.department_id == data.get("department"))
    if data.get("level"):
        query = query.filter(User.level == data.get("level"))
    if data.get("status"):
        query = query.filter(Payment.status == data.get("status"))
    if data.get("point"):
        query = query.filter(ClearanceItem.clearance_point_id == data.get("point"))
    if data.get("matric"):
        query = query.filter(User.matric_number == data.get("matric"))

    if data.get("date"):
        today = datetime.today().date()
        if data.get("date") == "today":
            query = query.filter(func.date(Payment.created_at) == today)
        elif data.get("date") == "yesterday":
            start = today - timedelta(days=1)
            query = query.filter(func.date(Payment.created_at) >= start)
        elif data.get("date") == "week":
            start = today - timedelta(days=7)
            query = query.filter(func.date(Payment.created_at) >= start)
        elif data.get("date") == "month":
            start = today.replace(day=1)
            query = query.filter(func.date(Payment.created_at) >= start)
    query = query.order_by(Payment.created_at.desc())

    page = data.get("page")
    limit = 20
    clearances = query.offset((page - 1) * limit).limit(limit).all()
    for payment in clearances:
        clear = Clearance.query.filter_by(payment_id=payment.id).first()
        data = {
            "id": payment.id,
            "student_name": payment.user.firstname + " " + payment.user.lastname,
            "amount": payment.amount,
            "department": payment.user.department.name,
            "department_id": payment.user.department_id,
            "matric": payment.user.matric_number,
            "email": payment.user.email,
            "for": clear.clearance_item.name if clear else "Refund",
            "to": clear.clearance_item.clearance_point.name if clear else "System",
            "office": clear.clearance_item.clearance_point.id if clear else "System",
            "created_at": payment.created_at,
            "level": payment.user.level,
            "status": payment.status,
        }
        if payment.system_payment == True:
            data["for"] = "System Payment"
            data["to"] = "System"
            data["office"] = "System"
            data["amount"] = 10000
        payments.append(data)

    total = f"{total:,}"
    return jsonify(
        {
            "message": "Got all payments successfully",
            "data": payments,
            "total": total,
            "all": length,
        }
    )


@bursar_route.route("/payments/department/<int:id>", methods=["GET"])
def get_all_department_payments(id):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["BURSAR", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    # clearance_items=ClearanceItem.query.filter_by(organization_id=user.get('organization_id'),payment_required=True)
    clearances = Clearance.query.all()
    payments = []
    total = 0
    for clearance in clearances:
        clearance_item = ClearanceItem.query.filter_by(
            id=clearance.clearance_item_id, payment_required=True, clearance_point_id=id
        ).first()
        if clearance_item:
            payment = Payment.query.filter_by(
                id=clearance.payment_id, status="paid"
            ).first()
            data = {
                "id": payment.id,
                "student_name": clearance.user.firstname
                + " "
                + clearance.user.lastname,
                "amount": clearance_item.amount,
                "department": clearance.user.department.name,
                "matric": clearance.user.matric_number,
                "email": clearance.user.email,
                "for": clearance_item.name,
                "to": clearance_item.clearance_point.name,
                "created_at": payment.created_at,
                "level": clearance.user.level,
            }
            payments.append(data)
            total = total + clearance_item.amount
    total = f"{total:,}"
    return jsonify(
        {"message": "Got all payments successfully", "data": payments, "total": total}
    )


@bursar_route.route("/analysis/payments", methods=["GET"])
def analysis_payments():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["BURSAR", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    # clearance_items=ClearanceItem.query.filter_by(organization_id=user.get('organization_id'),payment_required=True)
    clearances = Clearance.query.all()
    payments = []

    data = []
    departments = Department.query.filter_by(
        organization_id=user.get("organization_id")
    )
    for department in departments:
        payments = []
        total = 0
        for clearance in clearances:
            clearance_item = ClearanceItem.query.filter_by(
                id=clearance.clearance_item_id,
                payment_required=True,
                department_id=department.id,
            ).first()
            if clearance_item:
                payment = Payment.query.filter_by(
                    id=clearance.payment_id, status="paid"
                ).first()
                payments.append(payment)
                total = total + payment.amount
        data.append({"department": department.name, "total": total})

    return jsonify({"message": "Got all payments successfully", "data": data})


@bursar_route.route("payments/<id>", methods=["GET"])
def get_payments(id):
    payment = Payment.query.get(id)
    if not payment:
        return jsonify({"message": "Payment does not exist"})
    clearance = Clearance.query.filter_by(payment_id=payment.id).first()
    user = payment.user
    passport = PassPorts.query.filter_by(student_id=user.id).first()

    data = {
        "id": payment.id,
        "payment_id": payment.id,
        "desc": "System payment",
        "session": clearance.clearance_item.session.name if clearance else "General",
        "student_name": payment.user.firstname + " " + payment.user.lastname,
        "amount": payment.amount,
        "department": payment.user.department.name,
        "department_id": payment.user.department_id,
        "matric": payment.user.matric_number,
        "for": clearance.clearance_item.name if clearance else "System Payment",
        "to": clearance.clearance_item.clearance_point.name if clearance else "System",
        "office": clearance.clearance_item.clearance_point.id
        if clearance
        else "Cleara",
        "clearance_point": clearance.clearance_item.clearance_point.id
        if clearance
        else "Cleara",
        "created_at": payment.created_at,
        "level": payment.user.level,
        "status": payment.status,
        "payment_status": payment.status,
        "passport": "https://myclearance.qplusgnl.com/uploads/" + passport.file_url
        if passport
        else None,
    }
    if payment.system_payment == True:
        data["to"] = "System"
        data["for"] = "System Payment"
    return jsonify({"message": "Got all payments successfully", "data": data})
