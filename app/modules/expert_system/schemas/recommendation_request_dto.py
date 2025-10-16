from pydantic import BaseModel, Field
from typing import List, Optional


class PreferenceRequest(BaseModel):
    genres: List[str] = Field(default_factory=list, description="Géneros preferidos, p.ej. ['RPG','Action']")
    platforms: List[str] = Field(default_factory=list, description="Plataformas preferidas, p.ej. ['PC','PS5']")
    max_price: Optional[float] = Field(default=None, ge=0, description="Precio máximo dispuesto a pagar")
    allow_multiplayer: Optional[bool] = Field(default=None, description="¿Prefiere multijugador?")
    age_rating_max: Optional[int] = Field(default=None, ge=0, le=21, description="Edad máxima recomendada deseada")
    min_playtime_hours: Optional[int] = Field(default=None, ge=0, description="Horas mínimas de contenido deseadas")
    difficulty: Optional[str] = Field(default=None, description="Dificultad preferida: 'easy'|'normal'|'hard'")
    exclude_genres: List[str] = Field(default_factory=list, description="Géneros a evitar")
    exclude_platforms: List[str] = Field(default_factory=list, description="Plataformas a evitar")


class RecommendationRequest(BaseModel):
    user_id: Optional[int] = Field(default=None, description="Opcional: id de usuario para trazabilidad")
    preferences: PreferenceRequest
    limit: int = Field(default=5, ge=1, le=50)

