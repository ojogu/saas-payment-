from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.base.model import BaseModel


class Clearance(BaseModel):
    __tablename__ = "clearances"

    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    clearance_item_id: Mapped[int] = mapped_column(
        ForeignKey("clearance_items.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    payment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("payments.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    remark: Mapped[str] = mapped_column(String(255), default="No remark")

    # Relationships
    user: Mapped["User"] = relationship(back_populates="clearances")  # noqa: F821 # type: ignore
    payment: Mapped[Optional["Payment"]] = relationship(back_populates="clearance")  # noqa: F821 # type: ignore
    files: Mapped[List["Files"]] = relationship(  # noqa: F821 # type: ignore
        back_populates="clearance", cascade="all, delete-orphan"
    )
    clearance_item: Mapped["ClearanceItem"] = relationship(back_populates="clearances")  # noqa: F821 # type: ignore


class ClearanceLogs(BaseModel):
    __tablename__ = "clearance_logs"

    action: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    matric: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="clearance_logs")  # noqa: F821 # type: ignore
