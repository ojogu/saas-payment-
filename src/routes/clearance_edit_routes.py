import jwt
from flask import Blueprint, jsonify, request

from src.model import *

clearance_edits = Blueprint("clearance_edits", __name__, url_prefix="/clearance_edits")


@clearance_edits.route("/clearance_items_edit/create", methods=["POST"])
def create_clearance_item_edit():
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
    edit_type = data.get("edit_type")
    id = data.get("item_id")
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
    last_session = SchoolSession.query.get(session_id)

    if user.get("role") in ["SUBADMIN"]:
        clearance_point_id = user.get("clearance_point_id")
    if not last_session:
        return jsonify({"message": "No session"})

    update_data = {
        "levels": levels,
        "docs": added_docs,
        "departments": multi_departments,
        "officers": officers,
    }
    item_id = None
    if edit_type == "update":
        item_id = id
    new_item = ClearanceItemEdit(
        item_id=item_id,
        name=name,
        desc=description,
        organization_id=organization_id,
        clearance_point_id=clearance_point_id,
        all_level=all_level,
        is_global=is_global,
        is_multi=is_multi,
        payment_required=payment_required,
        document_required=document_required,
        amount=amount,
        account_id=account_id,
        session_id=last_session.id,
        is_passive=is_passive,
        multi_edits=update_data,
    )
    db.session.add(new_item)
    db.session.commit()

    return jsonify(
        {
            "status": "success",
            "message": "Edit made successfully the admin will approve soon",
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


@clearance_edits.route("/clearance_item_edit/<int:id>", methods=["GET"])
def get_clearance_item_edit(id):
    print(id)
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
    item = ClearanceItemEdit.query.get(id)
    multi_clearance = item.multi_edits["departments"]
    added_docs = item.multi_edits["docs"]
    officers = item.multi_edits["officers"]
    levels = item.multi_edits["levels"]
    docs = ClearanceDocuments.query.filter_by(clearance_item_id=id).all()
    for doc in docs:
        added_docs.append(doc.desc)
    if item:
        clearance_point = ClearancePoint.query.filter_by(
            id=item.clearance_point_id
        ).first()
        data = {
            "id": item.id,
            "name": item.name,
            "description": item.desc,
            "all_level": item.all_level,
            "levels": levels,
            "amount": item.amount,
            "is_global": item.is_global,
            "document_required": item.document_required,
            "department": clearance_point.name,
            "departments": multi_clearance,
            "docs": added_docs,
            "item_id": item.item_id,
            "officers": officers,
            "is_payment": item.payment_required,
            "is_multi": item.is_multi,
            "account_id": item.account_id,
            "clearance_point_id": item.clearance_point_id,
            "session": item.session_id,
            "is_passive": item.is_passive,
        }
        return jsonify(data), 200


@clearance_edits.route("/clearance_items_edits/get", methods=["GET"])
def get_clearance_items_edits():
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

    if not organization_id:
        return jsonify({"message": "organization is required"}), 400

    organization = Organization.query.filter_by(id=organization_id).first()
    if not organization:
        return jsonify({"message": "organization does not exist"}), 400

    if user.get("role") in ["ADMIN", "BURSAR", "SUBADMIN"]:
        query = ClearanceItemEdit.query.filter_by(organization_id=organization_id)

    if user.get("role") in ["SUBADMIN"]:
        clearance_point_id = user.get("clearance_point_id")
        query = ClearanceItemEdit.query.filter_by(
            clearance_point_id=clearance_point_id, organization_id=organization_id
        )

    items = query.all()
    results = []
    for item in items:
        if user.get("role") in ["SUBADMIN"]:
            officers = item.multi_edits["officers"]
            if user.get("id") not in officers:
                continue
        clearance_point = ClearancePoint.query.filter_by(
            id=item.clearance_point_id
        ).first()
        session = SchoolSession.query.get(item.session_id)
        data = {
            "id": item.id,
            "item_id": item.item_id,
            "name": item.name,
            "department": str(clearance_point.name).title(),
            "description": item.desc,
            "levels": item.multi_edits["levels"],
            "is_global": item.is_global,
            "is_payment": item.payment_required,
            "amount": f"{item.amount:,}" if item.amount else None,
            "account_id": item.account_id,
            "organization_id": item.organization_id,
            "clearance_point_id": item.clearance_point_id,
            "session": session.name,
            "all_level": item.all_level,
        }
        results.append(data)

    return jsonify({"data": results}), 200


@clearance_edits.route("/clearance_item_edit/<int:id>", methods=["DELETE"])
def clearance_edit_delete(id):
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
    item = ClearanceItemEdit.query.get(id)
    if item:
        db.session.delete(item)
        db.session.commit()

        return jsonify(
            {"message": "Clearance item edit deleted successfully", "status": "success"}
        ), 200
