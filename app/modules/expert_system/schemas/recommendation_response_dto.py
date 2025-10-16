from pydantic import BaseModel, Field
from typing import List


class RecommendationItem(BaseModel):
    id: int
    title: str
    genres: List[str]
    platforms: List[str]
    price: float
    age_rating: int = Field(description="Clasificación por edad, p.ej. 7, 12, 16, 18")
    playtime_hours: int
    difficulty: str
    multiplayer: bool
    score: float = Field(description="Puntaje de recomendación calculado por reglas")


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
    rules_applied: List[str]
    total: int

