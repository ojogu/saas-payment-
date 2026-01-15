
from typing import List, Optional
import uuid

from sqlalchemy import  ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.base.model import BaseModel


class Clearance(BaseModel):
    __tablename__ = "clearances"

    #fk
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=False)
    clearance_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("clearance_items.id"), nullable=False
    )
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("payments.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
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
    
    #fk
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="clearance_logs")  # noqa: F821 # type: ignore
