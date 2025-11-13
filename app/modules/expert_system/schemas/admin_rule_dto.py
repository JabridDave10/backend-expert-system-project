"""
Schemas para operaciones de administración de reglas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RuleCreateRequest(BaseModel):
    """Request para crear una nueva regla"""
    name: str = Field(..., description="Nombre único de la regla")
    description: str = Field(..., description="Descripción de qué hace la regla")
    conditions_json: List[dict] = Field(..., description="Lista de condiciones (IF)")
    actions_json: List[dict] = Field(..., description="Lista de acciones (THEN)")
    priority: int = Field(default=50, ge=0, le=100, description="Prioridad de ejecución (0-100)")
    category: Optional[str] = Field(None, description="Categoría de la regla")
    active: bool = Field(default=True, description="Si la regla está activa")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "RECOMMEND-Action-Game-123",
                "description": "Recomendar juego de acción si el usuario prefiere acción",
                "conditions_json": [
                    {
                        "entity": "user",
                        "attribute": "prefers_genre",
                        "operator": "==",
                        "value": "Action"
                    }
                ],
                "actions_json": [
                    {
                        "action": "assert_fact",
                        "entity": "recommendation_123",
                        "attribute": "game_id",
                        "value": 123,
                        "reason": "El usuario prefiere juegos de acción"
                    }
                ],
                "priority": 50,
                "category": "recommendation",
                "active": True
            }
        }


class RuleUpdateRequest(BaseModel):
    """Request para actualizar una regla existente"""
    name: Optional[str] = Field(None, description="Nombre único de la regla")
    description: Optional[str] = Field(None, description="Descripción de qué hace la regla")
    conditions_json: Optional[List[dict]] = Field(None, description="Lista de condiciones (IF)")
    actions_json: Optional[List[dict]] = Field(None, description="Lista de acciones (THEN)")
    priority: Optional[int] = Field(None, ge=0, le=100, description="Prioridad de ejecución (0-100)")
    category: Optional[str] = Field(None, description="Categoría de la regla")
    active: Optional[bool] = Field(None, description="Si la regla está activa")

    class Config:
        json_schema_extra = {
            "example": {
                "priority": 60,
                "active": False
            }
        }


class RuleResponse(BaseModel):
    """Response con información de una regla"""
    id: int
    name: str
    description: str
    conditions_json: List[dict]
    actions_json: List[dict]
    priority: int
    category: Optional[str]
    is_active: bool
    specificity: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RuleListResponse(BaseModel):
    """Response con lista paginada de reglas"""
    total: int = Field(..., description="Total de reglas en la base de datos")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    rules: List[RuleResponse] = Field(..., description="Lista de reglas")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 16047,
                "page": 1,
                "page_size": 50,
                "rules": []
            }
        }


class RuleDeleteResponse(BaseModel):
    """Response al eliminar una regla"""
    success: bool
    message: str
    rule_id: int

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Regla eliminada correctamente",
                "rule_id": 456
            }
        }


class RuleBulkDeleteRequest(BaseModel):
    """Request para eliminar múltiples reglas"""
    rule_ids: List[int] = Field(..., description="Lista de IDs de reglas a eliminar")

    class Config:
        json_schema_extra = {
            "example": {
                "rule_ids": [1, 2, 3, 4, 5]
            }
        }


class RuleBulkDeleteResponse(BaseModel):
    """Response al eliminar múltiples reglas"""
    success: bool
    message: str
    deleted_count: int
    failed_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Reglas eliminadas correctamente",
                "deleted_count": 5,
                "failed_count": 0
            }
        }
