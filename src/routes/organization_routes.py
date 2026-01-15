import json
import os
import uuid
from http import HTTPStatus
from flask import Blueprint, current_app, jsonify, request, send_from_directory
# from src.utils.db import db
from src.utils.response import success_response
from src.utils.config import allowed_file
from src.schema.organization import CreateOrganization, UpdateOrganization
from src.service.organization_service import OrganizationService


organization_routes = Blueprint("organization", __name__)




@organization_routes.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@organization_routes.route("/organizations", methods=["POST"])
def create_organization(organization_service: OrganizationService):
    #content-type - multipart/form-data
    data = request.form.to_dict()
    files = request.files.to_dict()
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")
    slogan = data.get("slogan")

    logo_filename = ""
    if "file" in request.files:
        file = request.files["file"]
        if file.filename != "" and allowed_file(file.filename):
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            logo_filename = file.filename

    validated_data = CreateOrganization(
        name=name,
        phone=phone,
        email=email,
        address=address,
        slogan=slogan,
        logo=logo_filename
    )

    
    organization = organization_service.create_organization(validated_data)
    return success_response(
            status_code=HTTPStatus.OK,
            message= "Organization created successfully",
            data = CreateOrganization(organization).model_dump()
        )




@organization_routes.route("/organizations", methods=["GET"])
def get_organizations(organization_service: OrganizationService):
    organizations = organization_service.fetch_all_organizations()
    data = []
    for org in organizations:
        org_data = {
                "id": org.id,
                "name": org.name,
                "phone": org.phone,
                "email": org.email,
                "users": len(org.users),
                "departments": len(org.departments),
                "faculties": len(org.faculties),
            }
        data.append(org_data)
        return success_response(
            status_code=HTTPStatus.OK,
            message="Successfully got all organizations",
            data=data
        )



@organization_routes.route("/organization/<id>", methods=["GET"])
def get_organization(id, organization_service: OrganizationService):
    organization_id = uuid.UUID(id)
    org = organization_service.fetch_one_organization(organization_id)
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
    return success_response(
            status_code=HTTPStatus.OK,
            message="Successfully got organization",
            data=org_data
        )



@organization_routes.route("/organization/<id>", methods=["PUT"])
def update_organization(id, organization_service: OrganizationService):
    organization_id = uuid.UUID(id)
        
        # Parse form data
    json_data = request.form.get("data")
    if not json_data:
            return jsonify({"message": "No data provided"}), 400
            
    data = json.loads(json_data)
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")
    slogan = data.get("slogan")
    logo = data.get("logo")

    # Handle file upload
    logo_filename = logo or ""
    if "file" in request.files:
        file = request.files["file"]
        if file.filename != "" and allowed_file(file.filename):
            filepath = os.path.join(current_app.confi["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            logo_filename = file.filename

     # Prepare update data
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if phone is not None:
        update_data["phone"] = phone
    if email is not None:
        update_data["email"] = email
    if address is not None:
        update_data["address"] = address
    if slogan is not None:
        update_data["slogan"] = slogan
    if logo_filename:
        update_data["logo"] = logo_filename

    organization = organization_service.update_organization(organization_id, update_data)
    return success_response(
            status_code=HTTPStatus.OK,
            message="Organization updated successfully",
            data=UpdateOrganization(
                name=organization.name,
                phone=organization.phone,
                email=organization.email,
                address=organization.address,
                slogan=organization.slogan,
                logo=organization.logo
            ).model_dump()
        )



@organization_routes.route("/organization/<id>", methods=["DELETE"])
def delete_organization(id, organization_service: OrganizationService):
    organization_id = uuid.UUID(id)
    organization_service.delete_organization(organization_id)
    return success_response(
            status_code=HTTPStatus.OK,
            message="Organization deleted successfully"
        )

