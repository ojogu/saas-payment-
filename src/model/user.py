from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.base.model import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firstname: Mapped[str] = mapped_column(String(80), nullable=False)
    lastname: Mapped[str] = mapped_column(String(80), nullable=False)
    middlename: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    matric_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, unique=True
    )
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    organization_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )
    faculty_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("faculties.id"), nullable=True
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    clearance_point_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("clearance_points.id"), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="users"
    )
    faculty: Mapped[Optional["Faculty"]] = relationship(back_populates="users")  # noqa: F821 # type: ignore
    department: Mapped[Optional["Department"]] = relationship(back_populates="users")  # noqa: F821 # type: ignore
    clearance_point: Mapped[Optional["ClearancePoint"]] = relationship(back_populates="users")  # noqa: F821 # type: ignore  
    clearances: Mapped[List["Clearance"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821 # type: ignore
    payments: Mapped[List["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821 # type: ignore
    passport: Mapped[List["PassPorts"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821 # type: ignore

    # def set_password(self, password: str) -> None:
    #     self.password_hash = generate_password_hash(
    #         password, method="pbkdf2:sha256", salt_length=12
    #     )

    # def check_password(self, password: str) -> bool:
    #     return check_password_hash(self.password_hash, password)
