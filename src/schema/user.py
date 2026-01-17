import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, UUID4
from src.model import Role_Enum, Level_Enum
class ValidateEmail(BaseModel):
    email: EmailStr
    
class CreateUser(BaseModel):
    id: Optional[UUID4] = None
    firstname: str
    lastname: str
    middlename: Optional[str] = None
    email: Optional[str] = None
    matric_number: Optional[str] = None
    phone_number: Optional[str] = None
    level: Optional[int] = None
    password: str
    role: Role_Enum
    organization_id: Optional[UUID4] = None
    faculty_id: Optional[UUID4] = None
    department_id: Optional[UUID4] = None
    clearance_point_id: Optional[UUID4] = None
    model_config = ConfigDict(from_attributes=True)
    
class UpdatePassword(BaseModel):
    user_id:uuid.UUID
    old_password:str
    new_password:str
    confirm_new_password:str
    model_config = ConfigDict(from_attributes=True)
