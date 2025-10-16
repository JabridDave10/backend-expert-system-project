from pydantic import BaseModel, Field
from typing import List, Optional


class HardwareConstraints(BaseModel):
    platform: Optional[str] = Field(default=None, description="Plataforma objetivo: PC, PS5, Xbox, Switch, etc.")
    min_ram_gb: Optional[int] = Field(default=None, ge=0)
    min_storage_gb: Optional[int] = Field(default=None, ge=0)


class BudgetConstraints(BaseModel):
    max_price: Optional[float] = Field(default=None, ge=0)


class TimeConstraints(BaseModel):
    min_playtime_hours: Optional[int] = Field(default=None, ge=0, description="Tiempo mínimo de juego deseado")
    max_playtime_hours: Optional[int] = Field(default=None, ge=0, description="Tiempo máximo disponible")


class ContentConstraints(BaseModel):
    allow_violence: Optional[bool] = Field(default=None)
    age_max: Optional[int] = Field(default=None, ge=0, le=21)
    multiplayer_required: Optional[bool] = Field(default=None)
    singleplayer_required: Optional[bool] = Field(default=None, description="Requiere modo single-player")
    coop_required: Optional[bool] = Field(default=None, description="Requiere modo cooperativo")
    pvp_required: Optional[bool] = Field(default=None, description="Requiere modo PvP/Competitivo")
    offline_required: Optional[bool] = Field(default=None, description="Prefiere juegos jugables offline")


class PreferenceConstraints(BaseModel):
    include_genres: List[str] = Field(default_factory=list)
    exclude_genres: List[str] = Field(default_factory=list)
    include_tags: List[str] = Field(default_factory=list, description="Tags requeridos")
    exclude_tags: List[str] = Field(default_factory=list, description="Tags a evitar")
    min_rating: Optional[float] = Field(default=None, ge=0, le=5, description="Rating mínimo")
    min_metacritic: Optional[int] = Field(default=None, ge=0, le=100, description="Metacritic score mínimo")


class DiagnoseRequest(BaseModel):
    hardware: HardwareConstraints = Field(default_factory=HardwareConstraints)
    budget: BudgetConstraints = Field(default_factory=BudgetConstraints)
    time: TimeConstraints = Field(default_factory=TimeConstraints)
    content: ContentConstraints = Field(default_factory=ContentConstraints)
    preferences: PreferenceConstraints = Field(default_factory=PreferenceConstraints)
    # Paginación
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=12, ge=1, le=50)
    # Compatibilidad: si se envía limit, usarlo como page_size
    limit: Optional[int] = Field(default=None, ge=1, le=50)
