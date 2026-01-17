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
from dishka.integrations.flask import inject, FromDishka
from werkzeug.utils import secure_filename
from src.utils.log import setup_logger
from src.base.exception import (
    BadRequest)
logger = setup_logger(__name__, "organization_route.log")
organization_routes = Blueprint("organization", __name__)


def validate_image(file):
    if not file:
        logger.warning("No image file provided for validation")
        raise BadRequest("No image provided")

    filename = secure_filename(file.filename)
    logger.info(f"Validating image file: {filename}")

    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}

    if '.' not in filename:
        logger.warning(f"File {filename} has no extension")
        raise BadRequest("File has no extension")

    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        logger.warning(f"Invalid file type for {filename}: {ext}. Allowed: {allowed_extensions}")
        raise BadRequest(f"Invalid file type. Allowed: {allowed_extensions}")

    # Check file size (e.g., max 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer

    if file_size > 5 * 1024 * 1024:  # 5MB
        logger.warning(f"File {filename} too large: {file_size} bytes")
        raise BadRequest("File too large. Max size: 5MB")

    logger.info(f"Image file {filename} validation successful")
    return True

def save_uploaded_file(file):
    """Safely save an uploaded file"""
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    # 1. Secure the filename
    filename = secure_filename(file.filename)

    # 2. Check if filename is empty (can happen with non-ASCII names)
    if not filename:
        filename = 'unnamed_file'
        logger.warning("Filename was empty after securing, using default: unnamed_file")

    # 3. Add UUID for uniqueness
    name, ext = os.path.splitext(filename)
    unique_filename = f"{uuid.uuid4().hex[:8]}_{name}{ext}"
    logger.info(f"Generated unique filename: {unique_filename}")

    # 4. Create full path
    filepath = os.path.join(upload_folder, unique_filename)

    # 5. Ensure upload directory exists
    os.makedirs(upload_folder, exist_ok=True)

    # 6. Save the file
    file.save(filepath)
    logger.info(f"File saved successfully at: {filepath}")

    return unique_filename

@organization_routes.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@organization_routes.route("/organizations", methods=["POST"])
@inject
def create_organization(organization_service: FromDishka[OrganizationService]):
    #protected route/rbac
    #content-type - multipart/form-data
    
    data = request.form.to_dict()
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")
    slogan = data.get("slogan")
    logo = request.files.get('logo')
    
    file_name = None
    if logo:
        #validate image
        validate_image(logo)
        file_name = save_uploaded_file(logo)


    logger.info(f"filename: {file_name}")
    validated_data = CreateOrganization(
        name=name,
        phone=phone,
        email=email,
        address=address,
        slogan=slogan,
        logo=file_name
    )

    
    organization = organization_service.create_organization(validated_data)
    # return organization.to_dict()
    return success_response(
            status_code=HTTPStatus.OK,
            message= "Organization created successfully",
            data = CreateOrganization.model_validate(organization).model_dump()
        )




@organization_routes.route("/organizations", methods=["GET"])
def fetch_all_organizations(organization_service: OrganizationService):
    organizations = organization_service.fetch_all_organizations()
    data = [CreateOrganization.model_validate(org).model_dump() for org in organizations]
    return success_response(
        status_code=HTTPStatus.OK,
        message="Successfully got all organizations",
        data=data
    )



@organization_routes.route("/organization/<id>", methods=["GET"])
def fetch_one_organization(id, organization_service: OrganizationService):
    organization_id = uuid.UUID(id)
    org = organization_service.fetch_one_organization(organization_id)
    data = CreateOrganization.model_validate(org).model_dump()
    return success_response(
        status_code=HTTPStatus.OK,
        message="Successfully got organization",
        data=data
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
    data = UpdateOrganization.model_validate(organization).model_dump()
    return success_response(
        status_code=HTTPStatus.OK,
        message="Organization updated successfully",
        data=data
    )



@organization_routes.route("/organization/<id>", methods=["DELETE"])
def delete_organization(id, organization_service: OrganizationService):
    organization_id = uuid.UUID(id)
    organization_service.delete_organization(organization_id)
    return success_response(
            status_code=HTTPStatus.OK,
            message="Organization deleted successfully"
        )
