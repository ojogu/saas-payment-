import jwt
import requests
from flask import Blueprint, current_app, jsonify, request

from src.model import Accounts, Notification_Setting, Organization
from src.utils.db import db

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/account_details/create", methods=["POST"])
def create_account():
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
    account_name = data.get("name")
    account_number = data.get("account_number")
    bank = data.get("bank")
    bank_name = data.get("bank_name")
    organization = Organization.query.filter_by(id=user.get("organization_id")).first()
    if not organization:
        return jsonify({"message": "organization not found"})
    if not account_name or not account_number or not bank:
        return jsonify({"message": "Missing Specific Details"})
    headers = {
        "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json",
    }
    payload = {
        "business_name": account_name,
        "settlement_bank": bank,
        "account_number": account_number,
        "percentage_charge": 5.0,
    }
    response = requests.post(
        "https://api.paystack.co/subaccount", headers=headers, json=payload
    )
    result = response.json()
    if result["status"] == True:
        new_account = Accounts(
            subaccount=result["data"]["subaccount_code"],
            account_number=account_number,
            account_name=account_name,
            bank=bank,
            bank_name=bank_name,
            organization_id=organization.id,
        )
        db
        db.add(new_account)
        db.commit()

        return jsonify({"status": "success", "message": "Account Created Successfully"})
    return jsonify({"message": "Invalid Account Details"})


@account_bp.route("/account_details/create/default", methods=["POST"])
def create_account_default():
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
        return jsonify({"message": "organization not found"})
    data = request.get_json()
    account_name = data.get("name")
    account_number = data.get("account_number")
    bank = data.get("bank")
    bank_name = data.get("bank_name")

    if not account_number or not bank or not account_name:
        return jsonify({"message": "Missing Specific Details"})
    headers = {
        "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json",
    }
    payload = {
        "business_name": account_name,
        "settlement_bank": bank,
        "account_number": account_number,
        "percentage_charge": 5.0,
    }
    response = requests.post(
        "https://api.paystack.co/subaccount", headers=headers, json=payload
    )
    result = response.json()
    if result["status"] == True:
        new_account = Accounts(
            subaccount=result["data"]["subaccount_code"],
            account_number=account_number,
            account_name=account_name,
            bank=bank,
            bank_name=bank_name,
            default_account=True,
            organization_id=organization.id,
        )
        db.session.add(new_account)
        db.session.commit()

        return jsonify(
            {"status": "success", "message": "Default Account Created Successfully"}
        )
    return jsonify({"message": "Invalid Account Details"})


@account_bp.route("accounts/all", methods=["GET"])
def get_all_accounts():
    try:
        SECRET_KEY = "balablu-01101"
        print(request.headers.get("Authorization"))
        decoded = jwt.decode(
            request.headers.get("Authorization"), SECRET_KEY, algorithms=["HS256"]
        )
        user = decoded
    except Exception:
        return jsonify({"message": "Invalid auth token"})
    if user.get("role") not in ["ADMIN", "BURSAR", "SUBADMIN", "AUDIT"]:
        return jsonify({"message": "Unauthorized Access"}), 401
    organization = user.get("organization_id")
    accounts = Accounts.query.filter_by(organization_id=organization)
    data = []
    for acc in accounts:
        acc_data = {
            "id": acc.id,
            "name": acc.account_name,
            "account_number": acc.account_number,
            "bank_name": acc.bank_name,
            "bank": acc.bank,
            "subaccount": acc.subaccount,
            "default": acc.default_account,
        }
        data.append(acc_data)
    default_account = Accounts.query.filter_by(default_account=True).first()
    if not default_account:
        return jsonify({"message": "no default"})
    return jsonify({"message": "success", "data": data})


@account_bp.route("/account/update/<id>", methods=["PUT"])
def update_accounts(id):
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
    item = Accounts.query.get(id)
    data = request.get_json()
    account_name = data.get("name")
    account_number = data.get("account_number")
    bank = data.get("bank")
    bank_name = data.get("bank_name")

    headers = {
        "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json",
    }
    payload = {
        "business_name": account_name,
        "settlement_bank": bank,
        "account_number": account_number,
        "percentage_charge": 5.0,
    }
    response = requests.post(
        "https://api.paystack.co/subaccount", headers=headers, json=payload
    )
    result = response.json()
    if result["status"] == True:
        item.subaccount = result["data"]["subaccount_code"]
        item.account_name = account_name
        item.account_number = account_number
        item.bank_name = bank_name
        item.bank = bank

        db.session.commit()

        return jsonify({"status": "success", "message": "Account Updated"})
    else:
        return jsonify({"message": "Invalid Account Details"})


@account_bp.route("accounts/<id>", methods=["DELETE"])
def delete_account(id):
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
    item = Accounts.query.get(id)

    if not item:
        return (jsonify({"error": "Account not found"}),)
    notification_settings = Notification_Setting.query.filter_by(account_id=id).first()
    if notification_settings:
        db.session.delete(notification_settings)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Account deleted successfully"}), 200
