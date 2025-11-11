"""
Fact DTOs - Data Transfer Objects para Hechos

Schemas de Pydantic para validación y serialización de hechos.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FactBase(BaseModel):
    """Schema base para hechos"""
    entity: str = Field(..., description="Entidad del hecho", example="user_1")
    attribute: str = Field(..., description="Atributo del hecho", example="age")
    value: str = Field(..., description="Valor del hecho", example="25")
    value_type: str = Field(default="string", description="Tipo del valor", example="int")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confianza (0.0-1.0)")
    source: str = Field(default="user_input", description="Fuente del hecho")


class CreateFactDTO(FactBase):
    """Schema para crear un hecho"""
    is_temporary: bool = Field(default=False, description="Si es temporal")
    session_id: Optional[int] = Field(None, description="ID de sesión si es temporal")


class FactDTO(FactBase):
    """Schema completo de un hecho (respuesta)"""
    id: int
    is_temporary: bool
    session_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateFactDTO(BaseModel):
    """Schema para actualizar un hecho"""
    value: Optional[str] = None
    value_type: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class FactListResponse(BaseModel):
    """Schema para respuesta de lista de hechos"""
    facts: list[FactDTO]
    total: int
    page: Optional[int] = 1
    page_size: Optional[int] = 100
