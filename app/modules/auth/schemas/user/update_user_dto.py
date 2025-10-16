from pydantic import BaseModel, EmailStr
from typing import Optional

class UpdateUserDto(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    id_status: Optional[bool] = None
