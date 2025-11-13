"""Game Model - Catálogo de Juegos en Base de Datos"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Game(Base):
    """
    Modelo de juego del catálogo.

    Almacena toda la información de los juegos disponibles para recomendar.
    Esta información se usa para enriquecer las recomendaciones del sistema experto.

    Atributos:
        id: ID único del juego (del catálogo RAWG)
        slug: Identificador URL-friendly
        name: Nombre del juego
        released: Fecha de lanzamiento
        tba: To Be Announced (si aún no tiene fecha)
        background_image: URL de la imagen principal
        rating: Rating promedio (0.0-5.0)
        rating_top: Rating máximo recibido
        ratings_count: Cantidad de ratings
        metacritic: Puntaje de Metacritic (0-100)
        playtime: Tiempo promedio de juego (horas)
        genres_json: Lista de géneros (JSON)
        platforms_json: Lista de plataformas (JSON)
        tags_json: Lista de tags (JSON)
        esrb_rating: Rating ESRB (Everyone, Teen, Mature, etc.)
        parent_platforms_json: Plataformas principales (JSON)
        stores_json: Tiendas donde está disponible (JSON)
        reviews_count: Cantidad de reviews
        added: Cantidad de usuarios que lo agregaron
        suggestions_count: Sugerencias relacionadas
        updated: Última actualización
        created_at: Timestamp de creación en BD
    """

    __tablename__ = "games"

    # Identificación
    id = Column(Integer, primary_key=True, index=True)  # ID del catálogo RAWG
    slug = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(500), nullable=False, index=True)

    # Fechas
    released = Column(String(50), nullable=True)  # Formato: "YYYY-MM-DD"
    tba = Column(Boolean, default=False)
    updated = Column(String(50), nullable=True)

    # Imágenes
    background_image = Column(Text, nullable=True)

    # Ratings y puntuaciones
    rating = Column(Float, default=0.0, index=True)
    rating_top = Column(Integer, default=0)
    ratings_count = Column(Integer, default=0)
    metacritic = Column(Integer, nullable=True, index=True)

    # Gameplay
    playtime = Column(Integer, default=0)  # Horas

    # Datos estructurados (JSON)
    genres_json = Column(JSON, nullable=True)  # [{"id": 4, "name": "Action", "slug": "action"}]
    platforms_json = Column(JSON, nullable=True)  # [{"platform": {...}, "released_at": "..."}]
    parent_platforms_json = Column(JSON, nullable=True)  # [{"platform": {"id": 1, "name": "PC"}}]
    tags_json = Column(JSON, nullable=True)  # [{"id": 31, "name": "Singleplayer"}]
    stores_json = Column(JSON, nullable=True)  # [{"id": 1, "store": {...}}]
    ratings_json = Column(JSON, nullable=True)  # [{"id": 5, "title": "exceptional", "count": 100}]

    # Clasificación
    esrb_rating = Column(String(50), nullable=True, index=True)  # "Everyone", "Teen", etc.

    # Estadísticas
    reviews_count = Column(Integer, default=0)
    reviews_text_count = Column(Integer, default=0)
    added = Column(Integer, default=0)
    suggestions_count = Column(Integer, default=0)

    # Colores dominantes (para UI)
    saturated_color = Column(String(10), nullable=True)
    dominant_color = Column(String(10), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    recommendations = relationship("Recommendation", back_populates="game")

    def __repr__(self):
        return f"<Game(id={self.id}, name='{self.name}', rating={self.rating})>"

    def to_dict(self):
        """Convierte el juego a diccionario"""
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "released": self.released,
            "tba": self.tba,
            "background_image": self.background_image,
            "rating": self.rating,
            "rating_top": self.rating_top,
            "ratings_count": self.ratings_count,
            "metacritic": self.metacritic,
            "playtime": self.playtime,
            "genres": self.genres_json,
            "platforms": self.platforms_json,
            "parent_platforms": self.parent_platforms_json,
            "tags": self.tags_json,
            "stores": self.stores_json,
            "ratings": self.ratings_json,
            "esrb_rating": self.esrb_rating,
            "reviews_count": self.reviews_count,
            "added": self.added,
            "suggestions_count": self.suggestions_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_genres_list(self) -> list:
        """Retorna lista de nombres de géneros"""
        if not self.genres_json:
            return []
        return [g.get("name", "") for g in self.genres_json]

    def get_platforms_list(self) -> list:
        """Retorna lista de nombres de plataformas"""
        if not self.platforms_json:
            return []
        return [p.get("platform", {}).get("name", "") for p in self.platforms_json]

    def get_tags_list(self) -> list:
        """Retorna lista de nombres de tags"""
        if not self.tags_json:
            return []
        return [t.get("name", "") for t in self.tags_json]

    def is_multiplayer(self) -> bool:
        """Verifica si el juego tiene multijugador"""
        tags = self.get_tags_list()
        multiplayer_keywords = ["Multiplayer", "Co-op", "Online Co-Op", "PvP", "MMO"]
        return any(keyword in tags for keyword in multiplayer_keywords)

    def is_singleplayer(self) -> bool:
        """Verifica si el juego tiene single player"""
        tags = self.get_tags_list()
        return "Singleplayer" in tags

    def is_suitable_for_age(self, min_age: int) -> bool:
        """
        Verifica si el juego es apropiado para una edad mínima.

        ESRB Ratings:
        - Everyone: 0+
        - Everyone 10+: 10+
        - Teen: 13+
        - Mature 17+: 17+
        - Adults Only 18+: 18+
        """
        if not self.esrb_rating:
            return True  # Si no tiene rating, asumimos que es apropiado

        esrb_age_map = {
            "Everyone": 0,
            "Everyone 10+": 10,
            "Teen": 13,
            "Mature 17+": 17,
            "Adults Only 18+": 18,
        }

        required_age = esrb_age_map.get(self.esrb_rating, 0)
        return min_age >= required_age

    def has_platform(self, platform_name: str) -> bool:
        """
        Verifica si el juego está disponible en una plataforma específica.

        Args:
            platform_name: Nombre de la plataforma (PC, PlayStation, Nintendo, Xbox)

        Returns:
            True si el juego está disponible en esa plataforma
        """
        if not self.parent_platforms_json:
            return False

        platforms = [p.get("platform", {}).get("name", "") for p in self.parent_platforms_json]
        return platform_name in platforms
