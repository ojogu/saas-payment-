from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.base.model import BaseModel

class Files(BaseModel):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clearance_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("clearances.id"), nullable=True
    )
    file_url: Mapped[Optional[str]] = mapped_column(
        String(250), nullable=True, unique=True
    )
    desc: Mapped[str] = mapped_column(String(250), nullable=False)

    # Relationships
    clearance: Mapped[Optional["Clearance"]] = relationship(back_populates="files")  # noqa: F821 # type: ignore


class PassPorts(BaseModel):
    __tablename__ = "passports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(
        String(250), nullable=True, unique=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="passport")  # noqa: F821 # type: ignore
