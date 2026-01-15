from typing import List, Optional
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.base.model import BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True, unique=True
    )
    logo: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, unique=True)
    email: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True, unique=True
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True, unique=True
    )
    slogan: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True, unique=True
    )


    # Relationships
    users: Mapped[List["User"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="organization", cascade="all, delete-orphan"
    )
    departments: Mapped[List["Department"]] = relationship(
        back_populates="organization", lazy=True, cascade="all, delete-orphan"
    )
    department_codes: Mapped[List["DepartmentCode"]] = relationship(
        back_populates="organization", lazy=True, cascade="all, delete-orphan"
    )
    clearance_points: Mapped[List["ClearancePoint"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="organization", lazy=True, cascade="all, delete-orphan"
    )
    clearance_logs: Mapped[List["ClearanceLogs"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="organization", lazy=True, cascade="all, delete-orphan"
    )
    faculties: Mapped[List["Faculty"]] = relationship(
        back_populates="organization", lazy=True, cascade="all, delete-orphan"
    )
    clearance_items: Mapped[List["ClearanceItem"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="organization", lazy=True, cascade="all, delete-orphan"
    )
    accounts: Mapped[List["Accounts"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="organization", lazy=True, cascade="all, delete-orphan"
    )
    #one to many relationship 
    school_sessions: Mapped[List["SchoolSession"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="organization", lazy=True, cascade="all, delete-orphan"
    )


class Faculty(BaseModel):
    __tablename__ = "faculties"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="faculties")
    users: Mapped[List["User"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="faculty", lazy=True, cascade="all, delete-orphan"
    )
    departments: Mapped[List["Department"]] = relationship(
        back_populates="faculty", lazy=True, cascade="all, delete-orphan"
    )


class Department(BaseModel):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    faculty_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("faculties.id"), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="departments")
    faculty: Mapped["Faculty"] = relationship(back_populates="departments")
    users: Mapped[List["User"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="department", lazy=True, cascade="all, delete-orphan"
    )
    department_code: Mapped[List["DepartmentCode"]] = relationship(
        back_populates="department"
    )
    multi_clearance_items: Mapped[List["MultiClearanceItem"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="department", lazy=True, cascade="all, delete-orphan"
    )


class DepartmentCode(BaseModel):
    __tablename__ = "department_code"

    code: Mapped[str] = mapped_column(String(10), nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("departments.id"), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        back_populates="department_codes"
    )
    department: Mapped["Department"] = relationship(back_populates="department_code")
