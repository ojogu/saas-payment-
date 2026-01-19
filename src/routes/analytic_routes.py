import io
from datetime import datetime, timedelta

import jwt
from flask import Blueprint, jsonify, request, send_file
from openpyxl import Workbook
from sqlalchemy import func
from src.utils.db import db
from src.model import *

analytics_route = Blueprint("analytics", __name__)


@analytics_route.route("/analytics", methods=["GET"])
def get_clearnce_analytics():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in [Role_Enum.ADMIN, Role_Enum.BURSAR, Role_Enum.SUPER_ADMIN, Role_Enum.SUB_ADMIN, Role_Enum.AUDIT]:
        return jsonify({"message": "Unauthorized Access"}), 401
    if user.get("role") in [Role_Enum.SUB_ADMIN, Role_Enum.BURSAR]:
        details = User.query.get(user.get("id"))
        organization_id = user.get("organization_id")
        query = db.session.query(Clearance).join(ClearanceItem).join(User)
        query = query.filter(User.organization_id == organization_id)
        query = query.filter(
            ClearanceItem.clearance_point_id == details.clearance_point_id
        )
        days = 30
        data = []
        while days >= 0:
            clearance_per_day = 0
            today = datetime.today().date()
            start = today - timedelta(days=days)
            result = query.filter(func.date(Clearance.created_at) == start)
            data.append({"day": start, "total": len(result.all())})
            days -= 1
        return jsonify({"message": "success", "data": data})
    data = []
    try:
        organizations = Organization.query.all()
        for org in organizations:
            faculties = Faculty.query.filter_by(organization_id=org.id).all()
            departments = Department.query.filter_by(organization_id=org.id).all()
            users = User.query.filter_by(organization_id=org.id).all()
            clearance_items = ClearanceItem.query.filter_by(
                organization_id=org.id
            ).all()
            org_data = {
                "name": org.name,
                "faculties": len(faculties),
                "departments": len(departments),
                "users": len(users),
                "clearance_items": len(clearance_items),
            }
            data.append(org_data)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"": str(e)}), 500


@analytics_route.route("/analytics/clearance", methods=["GET"])
def analytic_clearance():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "SUPERADMIN", "SUBADMIN", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    details = User.query.get(user.get("id"))
    organization_id = user.get("organization_id")
    query = db.session.query(Clearance).join(ClearanceItem).join(User)
    query = query.filter(User.organization_id == organization_id)
    if details.role == "SUBADMIN":
        query = query.filter(
            ClearanceItem.clearance_point_id == details.clearance_point_id
        )
    days = 30
    data = []
    while days >= 0:
        clearance_per_day = 0
        today = datetime.today().date()
        start = today - timedelta(days=days)
        result = query.filter(func.date(Clearance.created_at) == start)
        data.append({"day": start, "total": len(result.all())})
        days -= 1
    return jsonify({"message": "success", "data": data})


@analytics_route.route("/analytics/clearance/processed", methods=["GET"])
def analytic_processed():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "SUPERADMIN", "SUBADMIN", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    details = User.query.get(user.get("id"))
    organization_id = user.get("organization_id")
    query = db.session.query(Clearance).join(ClearanceItem).join(User)
    query = query.filter(User.organization_id == organization_id)
    query = query.filter(Clearance.status == "cleared")
    if details.role == "SUBADMIN":
        query = query.filter(
            ClearanceItem.clearance_point_id == details.clearance_point_id
        )
    days = 30
    data = []
    while days >= 0:
        clearance_per_day = 0
        today = datetime.today().date()
        start = today - timedelta(days=days)
        result = query.filter(func.date(Clearance.created_at) == start)
        data.append({"day": start, "total": len(result.all())})
        days -= 1
    return jsonify({"message": "success", "data": data})


@analytics_route.route("/analytics/income/office", methods=["POST"])
def analytic_income_office():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "SUPERADMIN", "SUBADMIN", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    details = User.query.get(user.get("id"))
    req = request.get_json()
    organization_id = user.get("organization_id")
    query = db.session.query(Payment).join(User).join(Clearance).join(ClearanceItem)
    query = query.filter(User.organization_id == organization_id)
    days = 30
    data = []

    if req.get("point_id"):
        query = query.filter(ClearanceItem.clearance_point_id == req.get("point_id"))
        clearance_items = ClearanceItem.query.filter_by(
            clearance_point_id=req.get("point_id")
        ).all()
        for clearance_item in clearance_items:
            income = 0
            clearance_per_day = 0
            today = datetime.today().date()
            start = today - timedelta(days=days)
            result = query.filter(Clearance.clearance_item == clearance_item)
            # result = query.filter(Payment.status == "paid")
            all = result.all()
            for payment in all:
                if payment.system_payment == True:
                    income += 10000
                else:
                    income += payment.amount
            data.append(
                {
                    "day": clearance_item.name,
                    "id": clearance_item.id,
                    "income": income,
                    "total": len(result.all()),
                }
            )
        data.reverse()
        return jsonify({"message": "success", "data": data})

    clearance_points = ClearancePoint.query.all()

    for clearance_point in clearance_points:
        income = 0
        clearance_per_day = 0
        today = datetime.today().date()
        start = today - timedelta(days=days)
        result = query.filter(ClearanceItem.clearance_point == clearance_point)
        # result = query.filter(Payment.status == "paid")
        all = result.all()
        for payment in all:
            if payment.system_payment == True:
                income += 10000
            else:
                income += payment.amount
        data.append(
            {
                "day": clearance_point.name,
                "income": income,
                "id": clearance_point.id,
                "total": len(result.all()),
            }
        )
    data.reverse()
    return jsonify({"message": "success", "data": data})


@analytics_route.route("/analytics/income", methods=["POST"])
def analytic_income():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "SUPERADMIN", "SUBADMIN", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    details = User.query.get(user.get("id"))
    req = request.get_json()
    organization_id = user.get("organization_id")
    query = db.session.query(Payment).join(User).join(Clearance).join(ClearanceItem)
    query = query.filter(User.organization_id == organization_id)
    if req.get("point_id"):
        query = query.filter(ClearanceItem.clearance_point_id == req.get("point_id"))
    days = 30
    data = []

    while days >= 0:
        income = 0
        clearance_per_day = 0
        today = datetime.today().date()
        start = today - timedelta(days=days)
        result = query.filter(func.date(Payment.created_at) == start)
        # result = query.filter(Payment.status == "paid")
        all = result.all()
        for payment in all:
            if payment.system_payment == True:
                income += 10000
            else:
                income += payment.amount
        data.append({"day": start, "income": income, "total": len(result.all())})
        days -= 1
    data.reverse()
    return jsonify({"message": "success", "data": data})


@analytics_route.route("/download-report", methods=["POST"])
def download_report():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["SUBADMIN", "STUDENT", "BURSAR", "ADMIN", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization_id = user.get("organization_id")
    details = User.query.get(user.get("id"))
    clearance_point = ClearancePoint.query.filter_by(
        id=details.clearance_point_id
    ).first()
    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"message": "Organization does not exist"})
    data = request.get_json()
    results = []
    query = db.session.query(Clearance).join(User)
    query = query.filter(User.organization_id == organization_id)
    if user.get("role") in ["BURSAR", "ADMIN"]:
        length = len(query.all())
    elif user.get("role") == "SUBADMIN":
        query = db.session.query(Clearance).join(ClearanceItem).join(User)
        query = query.filter(
            ClearanceItem.clearance_point_id == details.clearance_point_id
        )
        length = len(query.all())
    if data.get("department"):
        query = query.filter(User.department_id == data.get("department"))
    if data.get("level"):
        query = query.filter(User.level == data.get("level"))
    if data.get("status"):
        query = query.filter(Clearance.status == data.get("status"))
    if data.get("faculty"):
        query = query.filter(User.faculty_id == data.get("faculty"))

    if data.get("matric"):
        query = query.filter(User.matric_number == data.get("matric"))
    if data.get("is_doc"):
        query = query.filter(Clearance.files.any())

    if data.get("date"):
        today = datetime.today().date()
        if data.get("date") == "today":
            query = query.filter(func.date(Clearance.created_at) == today)
        elif data.get("date") == "yesterday":
            start = today - timedelta(days=1)
            query = query.filter(func.date(Clearance.created_at) >= start)
        elif data.get("date") == "week":
            start = today - timedelta(days=7)
            query = query.filter(func.date(Clearance.created_at) >= start)
        elif data.get("date") == "month":
            start = today.replace(day=1)
            query = query.filter(func.date(Clearance.created_at) >= start)
    else:
        print("")
        # if user.get("role") == "BURSAR":
        #     today = datetime.today().date()
        #     query =query.filter(func.date(Clearance.created_at) == today

    query = query.order_by(Clearance.created_at.desc())
    clearances = query.all()
    data = [
        [
            "ID",
            "Item Name",
            "Student Firstname",
            "Student Middlename",
            "Student Lastname",
            "Department",
            "Matric Number",
            "Level",
            "Status",
            "Office",
            "Date Created",
        ]
    ]
    for item in clearances:
        student = User.query.get(item.student_id)
        department = Department.query.filter_by(id=student.department_id).first()
        clearance_data = [
            item.id,
            item.clearance_item.name,
            student.firstname,
            student.middlename,
            student.lastname,
            department.name,
            student.matric_number,
            student.level,
            item.status,
            str(item.clearance_item.clearance_point.name).title(),
            str(item.created_at),
        ]
        data.append(clearance_data)
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    for row in data:
        ws.append(row)
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        download_name="report.xlsx",
        as_attachment=True,
    )


@analytics_route.route("/download-pay-report", methods=["POST"])
def download_payment_report():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["SUBADMIN", "STUDENT", "BURSAR", "ADMIN", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization_id = user.get("organization_id")
    details = User.query.get(user.get("id"))
    clearance_point = ClearancePoint.query.filter_by(
        id=details.clearance_point_id
    ).first()
    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"message": "Organization does not exist"})
    data = request.get_json()
    results = []
    query = db.session.query(Payment).join(User).join(Clearance).join(ClearanceItem)
    query = query.filter(User.organization_id == organization.id)
    if user.get("role") in ["BURSAR", "ADMIN"]:
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
    payments = query.all()
    data = [
        [
            "ID",
            "Student Firstname",
            "Student Middlename",
            "Student Lastname",
            "Department",
            "Matric Number",
            "Level",
            "Status",
            "Office",
            "Date Created",
            "For",
            "Amount",
        ]
    ]
    for item in payments:
        student = User.query.get(item.user_id)
        clearance = Clearance.query.filter_by(payment_id=item.id).first()
        department = Department.query.filter_by(id=student.department_id).first()
        clearance_data = [
            item.id,
            student.firstname,
            student.middlename,
            student.lastname,
            department.name,
            student.matric_number,
            student.level,
            item.status,
            str(clearance.clearance_item.clearance_point.name).title()
            if clearance
            else "System",
            str(item.created_at),
            clearance.clearance_item.name if clearance else "System Payment",
            item.amount,
        ]
        if item.system_payment == True:
            data[10] = "System Payment"
            data[11] = 10000
        data.append(clearance_data)
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    for row in data:
        ws.append(row)
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        download_name="payment_report.xlsx",
        as_attachment=True,
    )
