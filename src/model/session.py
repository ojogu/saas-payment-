from typing import List

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.base.model import BaseModel


class SchoolSession(BaseModel):
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="sessions")  # noqa: F821 # type: ignore
    clearance_items: Mapped[List["ClearanceItem"]] = relationship( #  noqa: F821 # type: ignore
        back_populates="session", lazy=True, cascade="all, delete-orphan"
    )  # noqa: F821 # type: ignore
