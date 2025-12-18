import random
import string
from datetime import datetime, timedelta

import jwt
import requests
from flask import Blueprint, current_app, jsonify, redirect, request
from sqlalchemy import func, or_

from src.model import *


def generate_payment_reference(prefix="ref", length=10):
    random_part = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=length)
    )
    return f"{prefix}-{random_part}"


clearance_bp = Blueprint("clearance", __name__, url_prefix="/clearance")


@clearance_bp.route("/clearance_items/create", methods=["POST"])
def create_clearance_item():
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
    data = request.get_json()
    name = data.get("name")
    is_global = data.get("is_global")
    is_multi = data.get("is_multi")
    payment_required = data.get("payment_required")
    document_required = data.get("document_required")
    organization_id = user.get("organization_id")
    clearance_point_id = data.get("clearance_point_id")
    description = data.get("description")
    levels = data.get("levels")
    all_level = data.get("all_level")
    amount = data.get("amount")
    account_id = data.get("account_id")
    multi_departments = data.get("multi_dept")
    session_id = data.get("session")
    added_docs = data.get("docs")
    officers = data.get("officers")
    is_passive = data.get("is_passive")
    last_session = Session.query.get(session_id)

    if user.get("role") in ["SUBADMIN"]:
        clearance_point_id = user.get("clearance_point_id")
    if not last_session:
        return jsonify({"message": "No session"})

    if is_global == True:
        is_multi = False

    if amount == 0 and payment_required == False:
        amount = None
        account_id = None
    elif amount != None and payment_required == True and amount != "":
        amount = int(amount)
    if not name or not organization_id or not clearance_point_id:
        return jsonify({"message": "Clearance Office is required"}), 400

    # Check if organization exists
    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"message": "Organization does not exist"}), 404

    # Optional: Check if department exists
    if clearance_point_id:
        clearance_point = ClearancePoint.query.filter_by(id=clearance_point_id).first()
        if not clearance_point:
            return jsonify({"message": "Invalid department_id"}), 404

    if is_passive == True:
        account_id = None
    new_item = ClearanceItem(
        name=name,
        desc=description,
        organization_id=organization.id,
        clearance_point_id=clearance_point.id,
        all_level=all_level,
        is_global=is_global,
        is_multi=is_multi,
        payment_required=payment_required,
        document_required=document_required,
        amount=amount,
        account_id=account_id,
        session_id=last_session.id,
        is_passive=is_passive,
    )

    db.session.add(new_item)
    db.session.commit()

    if is_multi == True:
        for dept in multi_departments:
            item = MultiClearanceItem(clearance_item_id=new_item.id, department_id=dept)
            db.session.add(item)
        db.session.commit()
    if all_level == False:
        for level in levels:
            item = MultiLevel(clearance_item_id=new_item.id, level=level)
            db.session.add(item)
        db.session.commit()
    if document_required == True:
        for doc in added_docs:
            item = ClearanceDocuments(clearance_item_id=new_item.id, desc=doc)
            db.session.add(item)
        db.session.commit()

    for officer in officers:
        new_officer = ClearanceOfficers(
            officer_id=officer,
            clearance_item_id=new_item.id,
        )
        db.session.add(new_officer)
    db.session.commit()

    new_log = ClearanceLogs(
        action=f"Created Clearance Item - {name}",
        email=user.get("email"),
        matric=user.get("matric_number"),
        role=user.get("role"),
        organization_id=organization.id,
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify(
        {
            "message": "Clearance item created successfully",
            "item": {
                "id": new_item.id,
                "name": new_item.name,
                "description": new_item.desc,
                "is_global": new_item.is_global,
                "organization_id": new_item.organization_id,
                "clearance_point_id": new_item.clearance_point_id,
                "account_id": new_item.account_id,
            },
        }
    ), 201


@clearance_bp.route("/clearance_item/<int:id>", methods=["GET"])
def get_clearance_item(id):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in [
        "ADMIN",
        "SUBADMIN",
        "STUDENT",
        "BURSAR",
        "DATA",
        "AUDIT",
    ]:
        return jsonify({"message": "Unauthorized Access"}), 401
    multi_clearance = []
    added_docs = []
    officers = []
    item = ClearanceItem.query.get(id)
    multi = MultiClearanceItem.query.filter_by(clearance_item_id=id).all()
    for mul in multi:
        multi_clearance.append(mul.department_id)
    old_officers = ClearanceOfficers.query.filter_by(clearance_item_id=id).all()
    for officer in old_officers:
        officers.append(officer.officer_id)
    docs = ClearanceDocuments.query.filter_by(clearance_item_id=id).all()
    for doc in docs:
        added_docs.append(doc.desc)
    if item:
        data = {
            "id": item.id,
            "name": item.name,
            "description": item.desc,
            "all_level": item.all_level,
            "levels": [level.level for level in item.multi_levels],
            "amount": item.amount,
            "is_global": item.is_global,
            "document_required": item.document_required,
            "department": item.clearance_point.name,
            "departments": multi_clearance,
            "docs": added_docs,
            "id": item.id,
            "officers": officers,
            "is_payment": item.payment_required,
            "is_multi": item.is_multi,
            "account_id": item.account_id,
            "subaccount": item.account.subaccount if item.account else None,
            "clearance_point_id": item.clearance_point_id,
            "session": item.session_id,
            "is_passive": item.is_passive,
        }
        return jsonify(data), 200


@clearance_bp.route("/clearance_items/get", methods=["GET"])
def get_clearance_items():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "SUBADMIN", "STUDENT", "BURSAR", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization_id = user.get("organization_id")
    clearance_point_id = user.get("clearance_point_id")
    level = user.get("level")
    if not organization_id:
        return jsonify({"message": "organization is required"}), 400
    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"message": "organization does not exist"}), 400
    if user.get("role") in ["SUBADMIN"]:
        query = ClearanceItem.query.filter_by(
            clearance_point_id=clearance_point_id, organization_id=organization_id
        )
        query = query.filter(
            ClearanceItem.clearance_officers.any(officer_id=user.get("id"))
        )
    if user.get("role") in ["ADMIN", "BURSAR", "AUDIT"]:
        query = ClearanceItem.query.filter_by(organization_id=organization_id)
    query2 = ClearanceItem.query.filter_by(is_global=True).all()

    items = query.all()
    results = []
    for item in items:
        clearance_point = ClearancePoint.query.filter_by(
            id=item.clearance_point_id
        ).first()
        data = {
            "id": item.id,
            "name": item.name,
            "department": str(clearance_point.name).title(),
            "description": item.desc,
            "levels": [level.level for level in item.multi_levels],
            "is_global": item.is_global,
            "is_payment": item.payment_required,
            "amount": f"{item.amount:,}" if item.amount else None,
            "account_id": item.account_id,
            "organization_id": item.organization_id,
            "clearance_point_id": item.clearance_point_id,
            "session": item.session.name,
            "all_level": item.all_level,
        }
        results.append(data)

    return jsonify({"data": results}), 200


@clearance_bp.route("/update_clearance_item/<int:item_id>", methods=["PUT"])
def update_clearance_item(item_id):
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
    data = request.get_json()
    item = ClearanceItem.query.get(item_id)

    if not item:
        return jsonify({"error": "Clearance item not found"}), 404

    # Update the item's details
    name = data.get("name")
    description = data.get("description")
    amount = data.get("amount")
    all_level = data.get("all_level")
    levels = data.get("levels")
    is_global = data.get("is_global")
    payment_required = data.get("payment_required")
    document_required = data.get("document_required")
    is_global = data.get("is_global")
    is_multi = data.get("is_multi")
    account_id = data.get("account_id")
    clearance_point_id = data.get("clearance_point_id")
    multi_departments = data.get("multi_dept")
    docs = data.get("docs")
    officers = data.get("officers")
    session_id = data.get("session")
    is_passive = data.get("is_passive")
    last_session = Session.query.get(session_id)
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization does not exist"}), 404
    if not last_session:
        return jsonify({"message": "No session"})
    item.session_id = session_id
    item.is_passive = is_passive
    if name != "":
        item.name = name
    if description != "":
        item.desc = description
    item.document_required = document_required

    if clearance_point_id != None and clearance_point_id != "":
        item.clearance_point_id = clearance_point_id

    item.is_global = is_global
    if is_global == True:
        is_multi = False

    if amount != None and type(amount) == int:
        amount = int(amount)
        item.amount = amount
    elif amount == None and type(amount) == int:
        item.amount = None
    if payment_required == False:
        item.amount = None
        item.account_id = None
        item.payment_required = False
        item.is_passive = False

    if payment_required == True:
        item.payment_required = True
        if amount != None:
            amount = int(amount)
            item.account_id = account_id

        else:
            return jsonify({"message": "Please enter an amount"})
    if is_passive == True:
        item.account_id = None

    if is_multi == True:
        multi = MultiClearanceItem.query.filter_by(clearance_item_id=item_id).all()
        for mul in multi:
            db.session.delete(mul)
        for dept in multi_departments:
            multi_item = MultiClearanceItem(
                clearance_item_id=item_id, department_id=dept
            )
            db.session.add(multi_item)
        item.is_multi = True

    elif is_multi == False:
        multi = MultiClearanceItem.query.filter_by(clearance_item_id=item_id).all()
        for mul in multi:
            db.session.delete(mul)
        item.is_multi = False

    if all_level == False:
        multi = MultiLevel.query.filter_by(clearance_item_id=item_id).all()
        for mul in multi:
            db.session.delete(mul)
        for level in levels:
            multi_item = MultiLevel(clearance_item_id=item_id, level=level)
            db.session.add(multi_item)
        item.all_level = False

    elif all_level == True:
        multi = MultiLevel.query.filter_by(clearance_item_id=item_id).all()
        for mul in multi:
            db.session.delete(mul)
        item.is_multi = True

    db.session.commit()

    if document_required == True:
        multi = ClearanceDocuments.query.filter_by(clearance_item_id=item_id).all()
        for mul in multi:
            db.session.delete(mul)
        for desc in docs:
            multi_item = ClearanceDocuments(clearance_item_id=item_id, desc=desc)
            db.session.add(multi_item)
        item.document_required = True
    elif document_required == False:
        multi = ClearanceDocuments.query.filter_by(clearance_item_id=item_id).all()
        for mul in multi:
            db.session.delete(mul)
        item.document_required = False

    db.session.commit()
    old_officers = ClearanceOfficers.query.filter_by(clearance_item_id=item_id).all()
    for officer in old_officers:
        db.session.delete(officer)
    for officer in officers:
        new_officer = ClearanceOfficers(
            officer_id=officer,
            clearance_item_id=item_id,
        )
        db.session.add(new_officer)
    db.session.commit()

    new_log = ClearanceLogs(
        action=f"Updated Clearance Item {item.name}",
        email=user.get("email"),
        matric=user.get("matric_number"),
        role=user.get("role"),
        organization_id=organization.id,
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify(
        {
            "message": "Clearance item updated successfully",
            "item": {
                "id": item.id,
                "name": item.name,
                "description": item.desc,
                "is_global": item.is_global,
                "organization_id": item.organization_id,
                "clearance_point_id": item.clearance_point_id,
                "account_id": item.account_id,
            },
        }
    ), 200


@clearance_bp.route("/clearance_items/<int:item_id>", methods=["DELETE"])
def delete_clearance_item(item_id):
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
        return jsonify({"message": "Organization does not exist"}), 404
    item = ClearanceItem.query.get(item_id)

    if not item:
        return jsonify({"error": "Clearance item not found"}), 404
    old_officers = ClearanceOfficers.query.filter_by(clearance_item_id=item_id).all()
    for officer in old_officers:
        db.session.delete(officer)
    multi = ClearanceDocuments.query.filter_by(clearance_item_id=item_id).all()
    for mul in multi:
        db.session.delete(mul)
    edits = ClearanceItemEdit.query.filter_by(item_id=item_id).all()
    for edit in edits:
        db.session.delete(edit)
    db.session.delete(item)
    db.session.commit()

    new_log = ClearanceLogs(
        action="Deleted Clearance Item",
        email=user.get("email"),
        matric=user.get("matric"),
        role=user.get("role"),
        organization_id=organization.id,
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({"message": "Clearance item deleted successfully"}), 200


@clearance_bp.route("clearance/payment/initiate/<id>", methods=["POST"])
def clearance_payment(id):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["STUDENT", "DATA"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    data = request.get_json()
    student_id = user.get("id")
    if user.get("role") == "DATA":
        student_id = data.get("student_id")
    clearance_item = ClearanceItem.query.get(id)
    payment_ref = generate_payment_reference()
    new_payment = Payment(
        user_id=student_id, payment_ref=payment_ref, amount=clearance_item.amount
    )
    db.session.add(new_payment)
    db.session.commit()
    link = f"{payment_ref}"

    return jsonify(
        {
            "message": "Payment Initiated Successfully",
            "link": link,
            "payment_id": new_payment.id,
            "subaccount": clearance_item.account.subaccount,
        }
    )


@clearance_bp.route("/clearance/create", methods=["POST"])
def create_clearance():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["STUDENT", "DATA"]:
        return jsonify({"message": "Unauthorized Access"}), 401

    data = request.get_json()
    student_id = user.get("id")
    if user.get("role") == "DATA":
        student_id = data.get("student_id")
    if not data.get("clearance-item"):
        return jsonify({"message": "Clearance Item ID is required"}), 400
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization not found"})
    existing_request = Clearance.query.filter_by(
        student_id=student_id, clearance_item_id=data["clearance-item"]
    ).first()
    if existing_request:
        return jsonify({"message": "You have already performed clearance on this item"})

    student = User.query.get(student_id)
    clearance_item = ClearanceItem.query.get(data.get("clearance-item"))
    if not clearance_item:
        return jsonify({"message": "Clearance Item does not exist"})
    if not student.matric_number:
        return jsonify({"message": "Student does not exist"})
    files = data.get("files")
    payment_id = data.get("payment_id")
    if clearance_item.organization_id != student.organization_id:
        # if clearance_item.department_id==student.department_id or clearance_item.is_global==True:
        #      files = data.get('files')
        #      payment_id=data.get('payment_id')
        # else:
        #     return jsonify({'message':'Wrong action'})
        return jsonify({"message": "No Organization"})

    if (
        payment_id
        and clearance_item.payment_required == True
        and clearance_item.is_passive == False
    ):
        payment = Payment.query.get(payment_id)
        headers = {
            "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
            "Content-Type": "application/json",
        }

        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{payment.payment_ref}",
            headers=headers,
        )
        result = response.json()
        if result["status"] and result["data"]["status"] == "success":
            status = "pending"
            paid_amount = result["data"]["amount"] / 100
            if paid_amount < clearance_item.amount:
                status = "partial"
                payment.amount = paid_amount
            else:
                status = "pending"
            payment.status = "paid"
            new_clearance = Clearance(
                student_id=student_id,
                clearance_item_id=data["clearance-item"],
                payment_id=payment_id,
                status=status,
            )
            db.session.add(new_clearance)
            db.session.commit()
        else:
            return jsonify({"message": "No payment made"})
    elif (
        payment_id
        and clearance_item.payment_required == True
        and clearance_item.is_passive == True
    ):
        payment = Payment.query.get(payment_id)
        status = "pending"
        if payment.amount < clearance_item.amount:
            status = "partial"

        else:
            status = "pending"
        payment.status = "paid"
        new_clearance = Clearance(
            student_id=student_id,
            clearance_item_id=data["clearance-item"],
            payment_id=payment_id,
            status=status,
        )
        db.session.add(new_clearance)
        db.session.commit()
    else:
        new_clearance = Clearance(
            student_id=student_id,
            clearance_item_id=data["clearance-item"],
            payment_id=payment_id,
        )
        db.session.add(new_clearance)
        db.session.commit()

    for file in files:
        new_file = Files(
            clearance_id=new_clearance.id, file_url=file["url"], desc=file["desc"]
        )
        db.session.add(new_file)
    db.session.commit()

    new_log = ClearanceLogs(
        action=f"Applied For {clearance_item.name}",
        email=user.get("email"),
        matric=user.get("matric_number"),
        role=user.get("role"),
        organization_id=organization.id,
    )
    db.session.add(new_log)
    db.session.commit()
    return jsonify(
        {"message": "Clearance created successfully", "data": new_clearance.id}
    ), 201


@clearance_bp.route("/clearance/complete/<id>", methods=["POST"])
def complete_clearance(id):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["STUDENT", "DATA"]:
        return jsonify({"message": "Unauthorized Access"}), 401

    data = request.get_json()
    student_id = user.get("id")
    if user.get("role") == "DATA":
        student_id = data.get("student_id")
    clearance = Clearance.query.get(id)
    item = clearance.clearance_item
    old_payment = clearance.payment
    new_payment = Payment.query.get(data.get("payment_id"))
    total = new_payment.amount + old_payment.amount
    organization = Organization.query.get(user.get("organization_id"))

    if total == item.amount:
        new_payment.amount = total
        new_payment.status = "paid"
        clearance.payment_id = new_payment.id
        clearance.status = "pending"
        new_log = ClearanceLogs(
            action=f"Completed Application For {item.name}",
            email=user.get("email"),
            matric=user.get("matric_number"),
            role=user.get("role"),
            organization_id=organization.id,
        )
        db.session.add(new_log)
        db.session.commit()
        return jsonify({"status": "success", "message": "Applied Successfully"})
    else:
        if total > item.amount:
            return jsonify({"messgae": "Payment amount to high"})
        if total < item.amount:
            return jsonify({"messgae": "Payment Incomplete"})


@clearance_bp.route("clearance/file/<path:filename>", methods=["GET"])
def serve_file(filename):
    url = "https://myclearance.qplusgnl.com/dotun/uploads/" + filename
    return redirect(url)


@clearance_bp.route("clearance/<int:id>", methods=["GET"])
def get_clearance(id):
    # try:
    #     SECRET_KEY="balablu-01101"
    #     decoded=jwt.decode(request.headers.get('Authorization'),SECRET_KEY,algorithms=["HS256"])
    #     user=decoded
    # except:
    #    return jsonify({"message":f"Invalid auth token"})
    # if user.get('role') not in ['SUBADMIN','STUDENT','BURSAR']:
    #     return jsonify({'message':"Unauthorized Access"}),401

    item = Clearance.query.get(id)
    clearance_item = ClearanceItem.query.get(item.clearance_item_id)
    payment = None
    if clearance_item.payment_required == True:
        payment = Payment.query.get(item.payment_id)
        ### paystack Block
    if not item:
        return jsonify({"message": "Clearance not found"})
    file_url = None
    uploaded = []
    clearance_item = ClearanceItem.query.get(item.clearance_item_id)
    if clearance_item.document_required == True:
        files = Files.query.filter_by(clearance_id=id).all()
        for file in files:
            url = "https://myclearance.qplusgnl.com/uploads/"
            file_url = f"{url}{file.file_url}"
            file_list = {"file_url": file_url, "desc": file.desc}
            uploaded.append(file_list)
    student = User.query.get(item.student_id)
    if not student or not student.matric_number:
        return jsonify({"message": "Student not found"})

    status = "No payment Required"
    if payment:
        status = payment.status
    officers = clearance_item.clearance_officers
    officer = User.query.get(officers[0].id)
    passport = PassPorts.query.filter_by(student_id=student.id).first()

    data = {
        "id": item.id,
        "name": clearance_item.name,
        "session": clearance_item.session.name,
        "department": student.department.name,
        "files": uploaded,
        "logo": request.host_url + "/api/uploads/" + student.organization.logo
        if student.organization.logo
        else None,
        "org": student.organization.name if student.organization.name else None,
        "student_name": str(student.firstname)
        + " "
        + str(student.lastname)
        + " "
        + str(student.middlename),
        "student_matric": student.matric_number,
        "student_department": student.department.name,
        "student_level": student.level,
        "clearance_point": clearance_item.clearance_point.name,
        "officer": officer.phone_number,
        "status": item.status,
        "clearance_item_id": item.clearance_item_id,
        "created_at": item.created_at,
        "payment_status": status,
        "payment_id": item.payment_id,
        "amount": payment.amount if payment else 0,
        "payment_required": clearance_item.payment_required,
        "document_required": clearance_item.document_required,
        "remark": item.remark,
        "passport": "https://myclearance.qplusgnl.com/uploads/" + passport.file_url
        if passport
        else None,
    }
    if payment and payment.amount < clearance_item.amount:
        amount = clearance_item.amount - payment.amount
        data["amount"] = amount
    return jsonify({"message": "sucessfully got clearance", "data": data})


@clearance_bp.route("clearance/clear/<int:id>", methods=["PUT"])
def clear_clearance(id):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "SUBADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization does not exist"}), 404
    data = request.get_json()
    item = Clearance.query.get(id)
    if not item:
        return jsonify({"message": "Clearance not found"})
    if item.status != "pending":
        return jsonify({"message": "Clearance request has already been processed"}), 400
    item.status = "cleared"
    item.remark = data.get("remark")
    db.session.commit()
    data = {
        "id": item.id,
        "student_id": item.student_id,
        "status": item.status,
        "clearance_item_id": item.clearance_item_id,
        "created_at": item.created_at,
    }

    new_log = ClearanceLogs(
        action=f"Cleared Student for {item.clearance_item.name}",
        email=user.get("email"),
        matric=user.get("matric_number"),
        role=user.get("role"),
        organization_id=organization.id,
    )
    db.session.add(new_log)
    db.session.commit()
    return jsonify({"message": "sucessfully cleared", "data": data})


@clearance_bp.route("clearance/reject/<int:id>", methods=["PUT"])
def reject_clearance(id):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "SUBADMIN"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization does not exist"}), 404
    item = Clearance.query.get(id)
    data = request.get_json()
    if not item:
        return jsonify({"error": "Clearance not found"})
    if item.status != "pending":
        return jsonify({"message": "Clearance request has already been processed"}), 400
    item.status = "rejected"
    item.remark = data.get("remark")
    db.session.commit()
    data = {
        "id": item.id,
        "student_id": item.student_id,
        "status": item.status,
        "clearance_item_id": item.clearance_item_id,
        "remark": data.get("remark"),
        "created_at": item.created_at,
    }
    new_log = ClearanceLogs(
        action=f"Rejected Student for {item.clearance_item.name}",
        email=user.get("email"),
        matric=user.get("matric_number"),
        role=user.get("role"),
        organization_id=organization.id,
    )
    db.session.add(new_log)
    db.session.commit()
    return jsonify({"message": "sucessfully rejected clearance", "data": data})


@clearance_bp.route("clearance/reapply/<int:id>", methods=["PUT"])
def reapply_clearance(id):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["STUDENT", "DATA"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "Organization does not exist"}), 404
    item = Clearance.query.get(id)
    if not item:
        return jsonify({"message": "Clearance not found"})
    if item.status != "rejected":
        return jsonify({"message": "You can only reapply for rejected requests"}), 400
    data = request.get_json()
    if item.clearance_item.document_required == True:
        files = Files.query.filter_by(clearance_id=id).all()
        for file in files:
            db.session.delete(file)
        db.session.commit()
        files = data.get("files")
        for file in files:
            new_file = Files(
                clearance_id=item.id, file_url=file.file_url, desc=file.desc
            )
            db.session.add(new_file)
    db.session.commit()

    item.status = "pending"
    db.session.commit()
    data = {
        "id": item.id,
        "student_id": item.student_id,
        "status": item.status,
        "clearance_item_id": item.clearance_item_id,
        "created_at": item.created_at,
    }
    new_log = ClearanceLogs(
        action=f"Repplied For {item.clearance_item.name}",
        email=user.get("email"),
        matric=user.get("matric_number"),
        role=user.get("role"),
        organization_id=organization.id,
    )
    db.session.add(new_log)
    db.session.commit()
    return jsonify({"message": "sucessfully reapplied", "data": data})


@clearance_bp.route("clearances/<int:id>", methods=["GET"])
def get_clearances(id):
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["SUBADMIN", "ADMIN", "BURSAR", "DATA", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    student = User.query.get(id)
    admin = User.query.get(user.get("id"))
    organization_id = student.organization_id
    department_id = student.department_id
    level = student.level
    organization = Organization.query.filter_by(id=organization_id).first()
    department = Department.query.filter_by(id=department_id).first()
    if not organization:
        return jsonify({"message": "Organization does not exist"})
    if not department_id or not department:
        return jsonify({"message": "Department does not exist"})
    sessions = (
        Session.query.filter_by(organization_id=organization.id)
        .order_by(Session.start_year.asc())
        .all()
    )
    session_ids = []
    for session in sessions:
        session_ids.append(session)
    active_session = session_ids[len(session_ids) - 1]
    current = active_session.start_year
    code = student.matric_number.split("/")
    year = 2000 + int(code[0])
    data = []
    current_level = int(level)

    while current_level > 0 and current >= year:
        session = Session.query.filter_by(start_year=current).first()
        if session:
            clearance_items = ClearanceItem.query.filter(
                ClearanceItem.session_id == session.id,
                or_(
                    ClearanceItem.multi_clearance_items.any(
                        department_id=student.department_id
                    ),
                    ClearanceItem.is_global == True,
                ),
                or_(
                    ClearanceItem.multi_levels.any(level=str(current_level)),
                    ClearanceItem.all_level == True,
                ),
            ).all()

            for clearance_item in clearance_items:
                clearance = Clearance.query.filter_by(
                    student_id=id, clearance_item_id=clearance_item.id
                ).first()
                item = {
                    "id": clearance_item.id,
                    "name": clearance_item.name,
                    "desc": clearance_item.desc,
                    "clearance_point_id": clearance_item.clearance_point_id,
                    "department": clearance_item.clearance_point.name,
                    "payment_required": clearance_item.payment_required,
                    "document_required": clearance_item.document_required,
                    "amount": clearance_item.amount,
                    "level": current_level,
                    "session": clearance_item.session.name,
                    "is_passive": clearance_item.is_passive,
                }
                if clearance:
                    item["status"] = clearance.status
                    item["id"] = clearance.id
                    item["remark"] = clearance.remark
                    item["payment_id"] = clearance.payment_id
                    if clearance.payment:
                        amt = clearance_item.amount - clearance.payment.amount
                        if amt != 0:
                            item["amount"] = amt
                        else:
                            item["amount"] = clearance.payment.amount
                    else:
                        item["amount"] = 0
                else:
                    item["status"] = "not cleared"
                if item not in data:
                    data.append(item)
        current_level = current_level - 100
        current = current - 1
    if user.get("role") == "SUBADMIN":
        return jsonify(
            {
                "message": "All clearance items fetched",
                "data": data,
                "clearance point": admin.clearance_point_id,
            }
        )
    return jsonify({"message": "All clearance items fetched", "data": data})


@clearance_bp.route("clearance/<int:id>", methods=["DELETE"])
def delete_clearance(id):
    item = Clearance.query.get(id)

    if not item:
        return jsonify({"message": "Clearance not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Clearance deleted successfully"}), 200


@clearance_bp.route("clearance/all", methods=["POST"])
def get_all_clearance():
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
    if user.get("role") in ["BURSAR", "ADMIN", "AUDIT"]:
        length = len(query.all())
    elif user.get("role") == "SUBADMIN":
        query = db.session.query(Clearance).join(ClearanceItem).join(User)
        query = query.filter(
            ClearanceItem.clearance_point_id == details.clearance_point_id
        )
        query = query.filter(
            ClearanceItem.clearance_officers.any(officer_id=user.get("id"))
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
    page = data.get("page")
    limit = 20
    clearances = query.offset((page - 1) * limit).limit(limit).all()
    for item in clearances:
        student = User.query.get(item.student_id)
        department = Department.query.filter_by(id=student.department_id).first()
        item_data = {
            "id": item.id,
            "name": item.clearance_item.name,
            "student_id": student.id,
            "first_name": student.firstname,
            "middle_name": student.middlename,
            "last_name": student.lastname,
            "department": department.name,
            "status": item.status,
            "level": student.level,
            "email": student.email,
            "matric_number": student.matric_number,
            "status": item.status,
            "date": item.created_at,
            "clearance_point_id": item.clearance_item.clearance_point_id,
            "date": item.created_at,
            "clearance_point": str(item.clearance_item.clearance_point.name).title(),
            "remark": item.remark,
            "files": [
                "https://myclearance.qplusgnl.com/uploads/" + file.file_url
                for file in item.files
            ],
        }
        results.append(item_data)
    if user.get("role") in ["SUBADMIN"]:
        return jsonify(
            {
                "message": f"sucessfully got all clearance in {clearance_point.name} department of {organization.name}",
                "data": results,
                "total": length,
            }
        )
    if user.get("role") in ["BURSAR", "ADMIN", "AUDIT"]:
        return jsonify(
            {
                "message": f"sucessfully got all clearance in {organization.name}",
                "data": results,
                "total": length,
            }
        )


@clearance_bp.route("clearance/student", methods=["GET"])
def get_all_student_clearance():
    try:
        SECRET_KEY = "balablu-01101"
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["STUDENT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    student = User.query.get(user.get("id"))
    organization_id = student.organization_id
    department_id = student.department_id
    level = student.level
    organization = Organization.query.filter_by(id=organization_id).first()
    department = Department.query.filter_by(id=department_id).first()
    if not organization:
        return jsonify({"message": "Organization does not exist"})
    if not department_id or not department:
        return jsonify({"message": "Department does not exist"})
    sessions = (
        Session.query.filter_by(organization_id=organization.id)
        .order_by(Session.start_year.asc())
        .all()
    )
    session_ids = []
    for session in sessions:
        session_ids.append(session)
    active_session = session_ids[len(session_ids) - 1]
    current = active_session.start_year

    code = student.matric_number.split("/")
    year = 2000 + int(code[0])
    data = []
    current_level = int(level)
    clearances = []
    system_payment = 12
    # system_payment = Payment.query.filter_by(user_id = student.id, system_payment = True).first()
    # if not system_payment:
    #     system_pay = {
    #         'name': 'System Payment',
    #         'status': 'not cleared'
    #     }
    #     data.append(system_pay)
    # else:
    #     system_pay = {
    #         'name': 'System Payment',
    #         'status': 'cleared',
    #         'amount':10000,
    #         'desc':'Payment to use the platform',
    #         'department':'Cleara',
    #         'payment_required':True,
    #     }
    #     data.append(system_pay)

    while current_level > 0 and current >= year:
        session = Session.query.filter_by(start_year=current).first()
        if session:
            clearance_items = ClearanceItem.query.filter(
                ClearanceItem.session_id == session.id,
                or_(
                    ClearanceItem.multi_clearance_items.any(
                        department_id=student.department_id
                    ),
                    ClearanceItem.is_global == True,
                ),
                or_(
                    ClearanceItem.multi_levels.any(level=str(current_level)),
                    ClearanceItem.all_level == True,
                ),
            ).all()

            for clearance_item in clearance_items:
                clearance = Clearance.query.filter_by(
                    student_id=user.get("id"), clearance_item_id=clearance_item.id
                ).first()
                item = {
                    "id": clearance_item.id,
                    "name": clearance_item.name,
                    "desc": clearance_item.desc,
                    "clearance_point_id": clearance_item.clearance_point_id,
                    "department": clearance_item.clearance_point.name,
                    "payment_required": clearance_item.payment_required,
                    "document_required": clearance_item.document_required,
                    "amount": clearance_item.amount,
                    "level": current_level,
                    "session": clearance_item.session.name,
                    "is_passive": clearance_item.is_passive,
                }
                if clearance:
                    item["status"] = clearance.status
                    item["id"] = clearance.id
                    item["remark"] = clearance.remark
                    item["payment_id"] = clearance.payment_id
                    if clearance.payment:
                        amt = clearance_item.amount - clearance.payment.amount
                        if amt != 0:
                            item["amount"] = amt
                        else:
                            item["amount"] = clearance.payment.amount
                    else:
                        item["amount"] = 0
                    clearances.append(item)
                else:
                    item["status"] = "not cleared"
                if item not in data:
                    data.append(item)
        current_level = current_level - 100
        current = current - 1
    if not system_payment:
        return jsonify(
            {
                "message": "All clearance items fetched",
                "data": data,
                "clearances": clearances,
                "system_payment": True,
            }
        )
    else:
        return jsonify(
            {
                "message": "All clearance items fetched",
                "data": data,
                "clearances": clearances,
            }
        )


@clearance_bp.route("/level")
def bulk_update_level():
    students = User.query.filter_by(role="STUDENT").all()
    for student in students:
        level = int(student.level)
        level = 100
        student.level = level
    db.session.commit()

    return "finished"
