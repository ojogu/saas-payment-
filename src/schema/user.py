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
