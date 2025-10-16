from pydantic import BaseModel
from typing import Optional

class CreateUserDto(BaseModel):
    firstName: str
    lastName: str
    username: str
    phone: str
    email: str
    password: str
    id_role: int
