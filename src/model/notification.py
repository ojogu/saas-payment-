from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.base.model import BaseModel


class Notification_Setting(BaseModel):
    __tablename__ = "notification_settings"

    price: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )


class Use_Notification(BaseModel):
    __tablename__ = "use_notifications"

    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    last_paid_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
