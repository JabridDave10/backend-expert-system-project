"""
Rule DTOs - Data Transfer Objects para Reglas

Schemas de Pydantic para validación y serialización de reglas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConditionSchema(BaseModel):
    """Schema para una condición de regla"""
    entity: str = Field(..., description="Entidad", example="user")
    attribute: str = Field(..., description="Atributo", example="age")
    operator: str = Field(..., description="Operador", example=">=")
    value: Any = Field(..., description="Valor esperado", example=18)


class ActionSchema(BaseModel):
    """Schema para una acción de regla"""
    action: str = Field(..., description="Tipo de acción", example="add_fact")
    entity: Optional[str] = Field(None, description="Entidad (para add_fact)")
    attribute: Optional[str] = Field(None, description="Atributo (para add_fact)")
    value: Optional[Any] = Field(None, description="Valor (para add_fact)")
    value_type: Optional[str] = Field(None, description="Tipo del valor")
    confidence: Optional[float] = Field(None, description="Confianza")
    game_id: Optional[int] = Field(None, description="ID de juego (para recommend)")
    reason: Optional[str] = Field(None, description="Razón (para recommend)")


class RuleBase(BaseModel):
    """Schema base para reglas"""
    name: str = Field(..., description="Nombre de la regla", max_length=255)
    description: Optional[str] = Field(None, description="Descripción de la regla")
    conditions: List[ConditionSchema] = Field(..., description="Condiciones IF", min_items=1)
    actions: List[ActionSchema] = Field(..., description="Acciones THEN", min_items=1)
    priority: int = Field(default=0, description="Prioridad de la regla")
    category: str = Field(default="general", description="Categoría de la regla", max_length=100)
    is_active: bool = Field(default=True, description="Si la regla está activa")


class CreateRuleDTO(RuleBase):
    """Schema para crear una regla"""
    pass


class RuleDTO(BaseModel):
    """Schema completo de una regla (respuesta)"""
    id: int
    name: str
    description: Optional[str]
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    priority: int
    specificity: int
    is_active: bool
    category: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UpdateRuleDTO(BaseModel):
    """Schema para actualizar una regla"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    conditions: Optional[List[ConditionSchema]] = None
    actions: Optional[List[ActionSchema]] = None
    priority: Optional[int] = None
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class RuleListResponse(BaseModel):
    """Schema para respuesta de lista de reglas"""
    rules: List[RuleDTO]
    total: int
    page: Optional[int] = 1
    page_size: Optional[int] = 100


class RuleSummaryDTO(BaseModel):
    """Schema resumido de una regla"""
    id: int
    name: str
    priority: int
    specificity: int
    is_active: bool
    category: str
    condition_count: int
    action_count: int

    class Config:
        from_attributes = True
