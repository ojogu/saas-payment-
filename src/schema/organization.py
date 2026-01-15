from typing import Any, Optional, Union
from pydantic import BaseModel, EmailStr, field_validator
from werkzeug.datastructures import FileStorage


class CreateOrganization(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    slogan: Optional[str] = None
    logo: Optional[Union[str, FileStorage]] = None

    model_config = {"arbitrary_types_allowed": True}


class UpdateOrganization(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    slogan: Optional[str] = None
    logo: Optional[Union[str, FileStorage]] = None

    model_config = {"arbitrary_types_allowed": True}
