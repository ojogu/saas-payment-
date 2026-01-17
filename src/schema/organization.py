from typing import Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, UUID4
from werkzeug.datastructures import FileStorage


class CreateOrganization(BaseModel):
    id: Optional[UUID4] = None
    name: str
    phone: Optional[str] = None
    email: EmailStr
    address: str
    slogan: Optional[str] = None
    logo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


    model_config = ConfigDict(from_attributes=True)


class UpdateOrganization(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    slogan: Optional[str] = None
    logo: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
