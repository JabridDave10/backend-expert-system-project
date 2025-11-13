"""
Schemas para operaciones de administración de juegos
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GameCreateRequest(BaseModel):
    """Request para crear un nuevo juego"""
    name: str = Field(..., description="Nombre del juego")
    slug: str = Field(..., description="Slug del juego para URLs")
    released: Optional[str] = Field(None, description="Fecha de lanzamiento (YYYY-MM-DD)")
    metacritic: Optional[int] = Field(None, ge=0, le=100, description="Puntuación Metacritic")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating del juego")
    genres_json: Optional[List[dict]] = Field(None, description="Lista de géneros")
    parent_platforms_json: Optional[List[dict]] = Field(None, description="Lista de plataformas")
    tags_json: Optional[List[dict]] = Field(None, description="Lista de tags")
    esrb_rating: Optional[str] = Field(None, description="Rating ESRB")
    background_image: Optional[str] = Field(None, description="URL de imagen de fondo")
    playtime: Optional[int] = Field(None, ge=0, description="Tiempo de juego promedio (horas)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "The Witcher 3: Wild Hunt",
                "slug": "the-witcher-3-wild-hunt",
                "released": "2015-05-19",
                "metacritic": 93,
                "rating": 4.66,
                "genres_json": [{"id": 4, "name": "Action", "slug": "action"}],
                "parent_platforms_json": [{"platform": {"id": 1, "name": "PC", "slug": "pc"}}],
                "tags_json": [{"id": 31, "name": "Singleplayer", "slug": "singleplayer"}],
                "esrb_rating": "Mature",
                "background_image": "https://media.rawg.io/media/games/...",
                "playtime": 46
            }
        }


class GameUpdateRequest(BaseModel):
    """Request para actualizar un juego existente"""
    name: Optional[str] = Field(None, description="Nombre del juego")
    slug: Optional[str] = Field(None, description="Slug del juego para URLs")
    released: Optional[str] = Field(None, description="Fecha de lanzamiento (YYYY-MM-DD)")
    metacritic: Optional[int] = Field(None, ge=0, le=100, description="Puntuación Metacritic")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating del juego")
    genres_json: Optional[List[dict]] = Field(None, description="Lista de géneros")
    parent_platforms_json: Optional[List[dict]] = Field(None, description="Lista de plataformas")
    tags_json: Optional[List[dict]] = Field(None, description="Lista de tags")
    esrb_rating: Optional[str] = Field(None, description="Rating ESRB")
    background_image: Optional[str] = Field(None, description="URL de imagen de fondo")
    playtime: Optional[int] = Field(None, ge=0, description="Tiempo de juego promedio (horas)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "The Witcher 3: Wild Hunt - GOTY",
                "metacritic": 94
            }
        }


class GameResponse(BaseModel):
    """Response con información de un juego"""
    id: int
    name: str
    slug: str
    released: Optional[str] = None
    metacritic: Optional[int] = None
    rating: Optional[float] = None
    genres_json: Optional[List[dict]] = None
    parent_platforms_json: Optional[List[dict]] = None
    tags_json: Optional[List[dict]] = None
    esrb_rating: Optional[str] = None
    background_image: Optional[str] = None
    playtime: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GameListResponse(BaseModel):
    """Response con lista paginada de juegos"""
    total: int = Field(..., description="Total de juegos en la base de datos")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    games: List[GameResponse] = Field(..., description="Lista de juegos")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "page": 1,
                "page_size": 20,
                "games": []
            }
        }


class GameDeleteResponse(BaseModel):
    """Response al eliminar un juego"""
    success: bool
    message: str
    game_id: int

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Juego eliminado correctamente",
                "game_id": 123
            }
        }
