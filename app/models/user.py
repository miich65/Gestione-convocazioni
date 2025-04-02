from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
class UserLogin(BaseModel):
    username: str
    password: str
    
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    
class UserInDB(UserBase):
    id: int
    password: str
    role: str = "arbitro"
    is_active: bool = True
    created_at: datetime
    
class User(UserBase):
    id: int
    role: str
    is_active: bool
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None