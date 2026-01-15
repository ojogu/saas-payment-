from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.base.model import BaseModel


class Accounts(BaseModel):
    __tablename__ = "accounts"

    subaccount: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    account_number: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    account_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    bank: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    default_account: Mapped[bool] = mapped_column(Boolean, default=False)
    
    #fk
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="accounts")  # noqa: F821 # type: ignore
    account_points: Mapped[List["AccountPoints"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    clearance_items: Mapped[List["ClearanceItem"]] = relationship( # noqa: F821 # type: ignore
        back_populates="account", lazy=True, cascade="all, delete-orphan"
    )  # noqa: F821 # type: ignore


class AccountPoints(BaseModel):
    __tablename__ = "account_points"

    clearance_point_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("clearance_points.id"), nullable=False
    )
    account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )

    # Relationships
    clearance_point: Mapped["ClearancePoint"] = relationship( # noqa: F821 # type: ignore
        back_populates="account_points"
    )  # noqa: F821 # type: ignore
    account: Mapped[Optional["Accounts"]] = relationship(
        back_populates="account_points"
    )


class Payment(BaseModel):
    __tablename__ = "payments"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_ref: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    system_payment: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, default=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="payments")  # noqa: F821 # type: ignore
    clearance: Mapped[List["Clearance"]] = relationship(back_populates="payment")  # noqa: F821 # type: ignore


class PassivePayment(BaseModel):
    __tablename__ = "passive_payments"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=False)
    payment_ref: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    clearance_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("clearance_items.id"), nullable=False
    )

    # Relationships
    clearance_item: Mapped["ClearanceItem"] = relationship( # noqa: F821 # type: ignore
        back_populates="passive_payments"
    )  # noqa: F821 # type: ignore
