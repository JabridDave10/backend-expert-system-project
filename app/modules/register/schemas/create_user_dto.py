from pydantic import BaseModel, Field
from typing import Optional

class CreateUserDto(BaseModel):
    firstName: str
    lastName: str
    username: str
    phone: str
    email: str
    password: str = Field(..., min_length=6, max_length=72)
    id_role: int
