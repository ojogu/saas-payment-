import json
import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from src.utils.db import db

from src.model import (
    Department,
    Faculty,
    Notification_Setting,
    Organization,
    User,
)

organization_routes = Blueprint("organization", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@organization_routes.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@organization_routes.route("/organization/create", methods=["POST"])
def create_organization():
    json_data = request.form.get("data")
    data = json.loads(json_data)
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")
    slogan = data.get("slogan")
    logo = data.get("logo")
    if Organization.query.filter_by(name=name).first():
        return jsonify({"message": "Organization already exists"}), 400
    if logo != "":
        if "file" not in request.files:
            return "No file part"

        file = request.files["file"]

        if file.filename == "":
            return "No selected file"

        if file and allowed_file(file.filename):
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
    organization = Organization(
        name=name, phone=phone, email=email, address=address, slogan=slogan, logo=logo
    )
    db.session.add(organization)
    db.session.commit()
    return jsonify(
        {
            "status": "success",
            "message": "Organization created successfully",
            "id": organization.id,
        }
    )


@organization_routes.route("/organizations/all", methods=["GET"])
def get_organizations():
    organizations = Organization.query.all()
    data = []
    for org in organizations:
        users = User.query.filter_by(organization_id=org.id).all()
        department = Department.query.filter_by(organization_id=org.id).all()
        faculty = Faculty.query.filter_by(organization_id=org.id).all()
        org_data = {
            "id": org.id,
            "name": org.name,
            "phone": org.phone,
            "email": org.email,
            "users": len(users),
        }
        data.append(org_data)
    return jsonify(
        {
            "status": "success",
            "message": "successfully got all organizations",
            "data": data,
        }
    )


@organization_routes.route("/organization/<id>", methods=["GET"])
def get_organization(id):
    org = Organization.query.get(id)
    if not org:
        return jsonify({"message": "Organization Does not exist"})
    org_data = {
        "id": org.id,
        "name": org.name,
        "phone": org.phone,
        "email": org.email,
        "slogan": org.slogan,
        "logo": request.host_url + "qplus/api/uploads/" + org.logo
        if org.logo
        else None,
        "address": org.address,
    }
    return jsonify({"status": "success", "data": org_data})


@organization_routes.route("/organization/<id>", methods=["PUT"])
def update_organization(id):
    org = Organization.query.get(id)
    if not org:
        return jsonify({"message": "Organization Does not exist"})
    json_data = request.form.get("data")
    data = json.loads(json_data)
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")
    slogan = data.get("slogan")
    logo = data.get("logo")

    org.name = name
    org.phone = phone
    org.email = email
    org.address = address
    org.slogan = slogan

    if logo != "":
        if "file" not in request.files:
            return "No file part"

        file = request.files["file"]

        if file.filename == "":
            return "No selected file"

        if file and allowed_file(file.filename):
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
    org.logo = logo

    db.session.commit()
    return jsonify({"status": "success", "message": "Successfully Updated"})


@organization_routes.route("/organization/<id>", methods=["DELETE"])
def delete_organization(id):
    item = Organization.query.get(id)

    if not item:
        return jsonify({"error": "Organization not found"}), 404

    notification_settings = Notification_Setting.query.filter_by(
        organization_id=id
    ).first()
    if notification_settings:
        db.session.delete(notification_settings)

    db.session.delete(item)
    db.session.commit()

    return jsonify(
        {"status": "success", "message": "Organization deleted successfully"}
    ), 200
