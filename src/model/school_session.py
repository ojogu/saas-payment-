from typing import List, Optional
from datetime import datetime
import uuid
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.base.model import BaseModel


class SchoolSession(BaseModel):
    __tablename__ = "school_sessions"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_year: Mapped[datetime] = mapped_column(Integer, nullable=False)
    end_year: Mapped[datetime] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )

    # Relationships
    #one to many relationship 
    organization: Mapped["Organization"] = relationship(back_populates="school_sessions")  # noqa: F821 # type: ignore
    clearance_items: Mapped[List["ClearanceItem"]] = relationship( #  noqa: F821 # type: ignore
        back_populates="school_session", lazy=True, cascade="all, delete-orphan"
    )  # noqa: F821 # type: ignore
