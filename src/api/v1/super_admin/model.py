from api.base.model import BaseModel
from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
class SuperAdmin(BaseModel):
    __tablename__ = 'superadmin'
    
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), default="SUPERADMIN")  # Optional, for clarity
    
    def __repr__(self):
        return f"<SuperAdmin(username='{self.username}', email='{self.email}')>"