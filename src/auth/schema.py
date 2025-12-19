
from typing import Optional

from pydantic import BaseModel, EmailStr


class Login(BaseModel):
    email: Optional[EmailStr] = None
    matric_number: Optional[str] = None
    password: str