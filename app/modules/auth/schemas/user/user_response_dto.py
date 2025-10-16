from pydantic import BaseModel
from typing import Optional

class UserResponseDto(BaseModel):
    id_user: int
    firstName: str
    lastName: str
    username: str
    phone: str
    email: str
    id_status: bool
    id_role: int
    createdAt: str
    updatedAt: str

    class Config:
        from_attributes = True
