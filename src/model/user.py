from datetime import datetime
from enum import IntEnum, StrEnum
from typing import List, Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.base.model import BaseModel

class Role_Enum(StrEnum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPERADMIN"
    SUB_ADMIN = "SUBADMIN"
    DATA = "DATA"
    BURSAR = "BURSAR"
    AUDIT = "AUDIT"
    
class Level_Enum(IntEnum):
    LEVEL_100 = 100
    LEVEL_200 = 200
    LEVEL_300 = 300
    LEVEL_400 = 400
    LEVEL_500 = 500
    
class User(BaseModel):
    __tablename__ = "users"

    firstname: Mapped[str] = mapped_column(String(80), nullable=False)
    lastname: Mapped[str] = mapped_column(String(80), nullable=False)
    middlename: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, unique=True, index=True)
    matric_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, unique=True, index=True
    )
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[Optional[Level_Enum]] = mapped_column(
        SqlEnum(Level_Enum, name="level_enum"),  nullable=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[Role_Enum] = mapped_column(
        SqlEnum(Role_Enum, name="role_enum"),  nullable=False)
    
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )
    faculty_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("faculties.id"), nullable=True
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    clearance_point_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("clearance_points.id"), nullable=True, default=None
    )


    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="users"
    )
    faculty: Mapped[Optional["Faculty"]] = relationship(back_populates="users")  # noqa: F821 # type: ignore
    department: Mapped[Optional["Department"]] = relationship(back_populates="users")  # noqa: F821 # type: ignore
    clearance_point: Mapped[Optional["ClearancePoint"]] = relationship( # noqa: F821 # type: ignore
        back_populates="users"
    )  # noqa: F821 # type: ignore
    clearances: Mapped[List["Clearance"]] = relationship( # noqa: F821 # type: ignore
        back_populates="user", cascade="all, delete-orphan" 
    )  
    payments: Mapped[List["Payment"]] = relationship( # noqa: F821 # type: ignore
        back_populates="user", cascade="all, delete-orphan"
    )  # noqa: F821 # type: ignore
    passport: Mapped[List["PassPorts"]] = relationship( # noqa: F821 # type: ignore
        back_populates="user", cascade="all, delete-orphan"
    )  # noqa: F821 # type: ignore
