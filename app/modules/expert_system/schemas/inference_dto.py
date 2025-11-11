"""
Inference DTOs - Data Transfer Objects para Inferencia

Schemas de Pydantic para validación y serialización de sesiones de inferencia.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class InitialFactSchema(BaseModel):
    """Schema para un hecho inicial de inferencia"""
    entity: str = Field(..., description="Entidad", example="user")
    attribute: str = Field(..., description="Atributo", example="prefers_genre")
    value: Any = Field(..., description="Valor", example="RPG")
    value_type: str = Field(default="string", description="Tipo del valor")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confianza")


class InferenceRequestDTO(BaseModel):
    """Schema para solicitud de inferencia"""
    initial_facts: List[InitialFactSchema] = Field(..., description="Hechos iniciales", min_items=1)
    goal: str = Field(default="recommend_game", description="Objetivo de la inferencia")
    max_iterations: int = Field(default=100, ge=1, le=1000, description="Máximo de iteraciones")
    conflict_strategy: str = Field(
        default="combined",
        description="Estrategia de resolución de conflictos",
        pattern="^(priority|specificity|recency|combined)$"
    )
    active_rules_only: bool = Field(default=True, description="Solo usar reglas activas")


class ConclusionSchema(BaseModel):
    """Schema para una conclusión"""
    type: str
    game_id: Optional[int] = None
    attribute: Optional[str] = None
    value: Optional[Any] = None
    confidence: float


class RuleFiredSchema(BaseModel):
    """Schema para una regla disparada"""
    iteration: int
    rule_id: int
    rule_name: str
    rule_priority: int
    facts_matched_count: int
    facts_added_count: int


class InferenceResponseDTO(BaseModel):
    """Schema para respuesta de inferencia"""
    session_id: int
    success: bool
    status: str
    goal: str
    iterations: int
    execution_time: float
    conclusions: List[ConclusionSchema]
    recommendations: List[Dict[str, Any]]
    rules_fired_count: int
    explanation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SessionDTO(BaseModel):
    """Schema para una sesión de inferencia"""
    id: int
    user_id: Optional[int]
    status: str
    goal: str
    iterations_performed: int
    confidence: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema para lista de sesiones"""
    sessions: List[SessionDTO]
    total: int
    page: Optional[int] = 1
    page_size: Optional[int] = 10


class ExplanationResponseDTO(BaseModel):
    """Schema para explicación de inferencia"""
    session_id: int
    status: str
    goal: str
    iterations: int
    confidence: int
    created_at: Optional[str]
    completed_at: Optional[str]
    conclusions: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    explanation: Dict[str, Any]
