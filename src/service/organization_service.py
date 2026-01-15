import uuid
from src.schema.organization import CreateOrganization
# from src.utils.db import db
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from src.model import Organization, Notification_Setting
from src.utils.log import setup_logger
from src.utils.exception import (
    AlreadyExistsError,
    DatabaseError,
    NotFoundError
)

logger = setup_logger(__name__, "organization.log")

class OrganizationService():
    def __init__(self, db: Session):
        self.db = db 
    
    def check_if_organization_exist_by_name(self, organization_name:str):
        try:
            stmt = self.db.execute(
                select(Organization).where(
                    func.lower(Organization.name) == organization_name.lower()
                )
            )
            organization = stmt.scalar_one_or_none()
            return organization
        except SQLAlchemyError as e:
            logger.error(f"Error checking organization existence by name '{organization_name}': {str(e)}")
            raise DatabaseError()
        
    def check_if_organization_exist_by_id(self, organization_id: uuid.UUID):
        try:
            stmt = self.db.execute(
                select(Organization).where(
                    Organization.id == organization_id
                )
            )
            organization = stmt.scalar_one_or_none()
            return organization
        except SQLAlchemyError as e:
            logger.error(f"Error checking organization existence by id '{organization_id}': {str(e)}")
            raise DatabaseError()
    
    def create_organization(self, organization_data:CreateOrganization):
        existing = self.check_if_organization_exist_by_name(organization_data.name)
        if existing:
            raise AlreadyExistsError("Organization with this name already exists")
        organization = Organization(
            name=organization_data.name,
            phone=organization_data.phone,
            email=organization_data.email,
            address=organization_data.address,
            slogan=organization_data.slogan,
            logo=organization_data.logo
        )
        self.db.add(organization)
        self.db.commit()
        return organization

    def fetch_all_organizations(self):
        try:
            stmt = self.db.execute(
                select(Organization).options(
                    selectinload(Organization.users),
                    selectinload(Organization.departments),
                    selectinload(Organization.department_codes),
                    selectinload(Organization.clearance_points),
                    selectinload(Organization.clearance_logs),
                    selectinload(Organization.faculties),
                    selectinload(Organization.clearance_items),
                    selectinload(Organization.accounts),
                    selectinload(Organization.school_sessions)
                )
            )
            organizations = stmt.scalars().all()
            return organizations
        except SQLAlchemyError as e:
            logger.error(f"Error fetching all organizations: {str(e)}")
            raise DatabaseError()

    def fetch_one_organization(self, organization_id: uuid.UUID):
        organization = self.check_if_organization_exist_by_id(organization_id)
        if not organization:
            raise NotFoundError("Organization not found")
        return organization

    def update_organization(self, organization_id: uuid.UUID, update_data: dict):
        organization = self.check_if_organization_exist_by_id(organization_id)
        if not organization:
            raise NotFoundError("Organization not found")
        for key, value in update_data.items():
            if hasattr(organization, key):
                setattr(organization, key, value)
        try:
            self.db.commit()
            return organization
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating organization {organization_id}: {str(e)}")
            raise DatabaseError()

    def delete_organization(self, organization_id: uuid.UUID):
        organization = self.check_if_organization_exist_by_id(organization_id)
        if not organization:
            raise NotFoundError("Organization not found")
        try:
            notification_settings = self.db.execute(
                select(Notification_Setting).where(Notification_Setting.organization_id == organization_id)
            ).scalar_one_or_none()
            if notification_settings:
                self.db.delete(notification_settings)
            self.db.delete(organization)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting organization {organization_id}: {str(e)}")
            raise DatabaseError()
