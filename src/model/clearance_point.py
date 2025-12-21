from typing import List, Optional
from sqlalchemy import String, Integer, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.base.model import BaseModel


class ClearancePoint(BaseModel):
    __tablename__ = "clearance_points"
    
    
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="clearance_points")  # pyright: ignore[reportUndefinedVariable] # noqa: F821
    account_points: Mapped[List["AccountPoints"]] = relationship(back_populates="clearance_point", lazy=True, cascade="all, delete-orphan")  # pyright: ignore[reportUndefinedVariable] # noqa: F821
    users: Mapped[List["User"]] = relationship(back_populates="clearance_point", lazy=True, cascade="all, delete-orphan")  # pyright: ignore[reportUndefinedVariable] # noqa: F821
    clearance_items: Mapped[List["ClearanceItem"]] = relationship(back_populates="clearance_point", lazy=True, cascade="all, delete-orphan")


class ClearanceItem(BaseModel):
    __tablename__ = "clearance_items"
    
    
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    desc: Mapped[str] = mapped_column(String(250), nullable=False)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    document_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_multi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_passive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    all_level: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    clearance_point_id: Mapped[int] = mapped_column(ForeignKey("clearance_points.id"), nullable=False)
    school_session_id: Mapped[int] = mapped_column(ForeignKey("school_sessions.id"), nullable=False)
    account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="clearance_items") # type: ignore  # noqa: F821
    clearance_point: Mapped["ClearancePoint"] = relationship(back_populates="clearance_items")
    clearances: Mapped[List["Clearance"]] = relationship(back_populates="clearance_item", cascade="all, delete-orphan") # type: ignore  # noqa: F821
    passive_payments: Mapped[List["PassivePayment"]] = relationship(back_populates="clearance_item", cascade="all, delete-orphan")  # type: ignore # noqa: F821
    multi_clearance_items: Mapped[List["MultiClearanceItem"]] = relationship(back_populates="clearance_item", cascade="all, delete-orphan")
    clearance_officers: Mapped[List["ClearanceOfficers"]] = relationship(back_populates="clearance_item", cascade="all, delete-orphan")
    school_session: Mapped["SchoolSession"] = relationship(back_populates="clearance_items")  # type: ignore # noqa: F821
    account: Mapped[Optional["Accounts"]] = relationship(back_populates="clearance_items")  # type: ignore # noqa: F821
    multi_levels: Mapped[List["MultiLevel"]] = relationship(back_populates="clearance_item", cascade="all, delete-orphan")


class ClearanceItemEdit(BaseModel):
    __tablename__ = "clearance_item_edit"
    
    
    item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clearance_items.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    desc: Mapped[str] = mapped_column(String(250), nullable=False)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    document_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_multi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_passive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    all_level: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    multi_edits: Mapped[Optional[dict]] = mapped_column(JSON)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    clearance_point_id: Mapped[int] = mapped_column(ForeignKey("clearance_points.id"), nullable=False)
    session_id: Mapped[Optional[int]] = mapped_column(Integer)
    account_id: Mapped[Optional[int]] = mapped_column(Integer)


class ClearanceOfficers(BaseModel):
    __tablename__ = "clearance_officers"
    officer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    clearance_item_id: Mapped[int] = mapped_column(ForeignKey("clearance_items.id"), nullable=False)
    
    # Relationships
    clearance_item: Mapped["ClearanceItem"] = relationship(back_populates="clearance_officers")


class MultiClearanceItem(BaseModel):
    __tablename__ = "multi_clearance_item"
    
    clearance_item_id: Mapped[int] = mapped_column(ForeignKey("clearance_items.id"), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    
    # Relationships
    department: Mapped["Department"] = relationship(back_populates="multi_clearance_items")  # pyright: ignore[reportUndefinedVariable] # noqa: F821
    clearance_item: Mapped["ClearanceItem"] = relationship(back_populates="multi_clearance_items")


class MultiLevel(BaseModel):
    __tablename__ = "multi_levels"
    
    
    clearance_item_id: Mapped[int] = mapped_column(ForeignKey("clearance_items.id"), nullable=False)
    level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Relationships
    clearance_item: Mapped["ClearanceItem"] = relationship(back_populates="multi_levels")


class ClearanceDocuments(BaseModel):
    __tablename__ = "clearance_document"
    
    
    desc: Mapped[str] = mapped_column(String(250), nullable=False)
    clearance_item_id: Mapped[int] = mapped_column(ForeignKey("clearance_items.id"), nullable=False)
