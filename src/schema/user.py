import uuid
from pydantic import BaseModel, EmailStr

class ValidateEmail(BaseModel):
    email: EmailStr
    
class CreateUser(BaseModel):
    firstname: str
    lastname: str
    email: str
    phone: str
    password: str = "super-admin-default@123"
    role: str

class UpdatePassword(BaseModel):
    user_id:uuid.UUID
    old_password:str
    new_password:str
    confirm_new_password:str