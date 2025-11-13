"""
Servicio de administración de juegos
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Tuple
from datetime import datetime

from app.modules.expert_system.models.game import Game
from app.modules.expert_system.schemas.admin_game_dto import (
    GameCreateRequest,
    GameUpdateRequest
)


class AdminGameService:
    """Servicio para operaciones CRUD de juegos"""

    @staticmethod
    def create_game(db: Session, game_data: GameCreateRequest) -> Game:
        """
        Crear un nuevo juego en la base de datos

        Args:
            db: Sesión de base de datos
            game_data: Datos del juego a crear

        Returns:
            Game: Juego creado

        Raises:
            ValueError: Si ya existe un juego con ese slug
        """
        # Verificar si ya existe un juego con ese slug
        existing_game = db.query(Game).filter(Game.slug == game_data.slug).first()
        if existing_game:
            raise ValueError(f"Ya existe un juego con el slug '{game_data.slug}'")

        # Crear el juego
        new_game = Game(
            name=game_data.name,
            slug=game_data.slug,
            released=game_data.released,
            metacritic=game_data.metacritic,
            rating=game_data.rating,
            genres_json=game_data.genres_json,
            parent_platforms_json=game_data.parent_platforms_json,
            tags_json=game_data.tags_json,
            esrb_rating=game_data.esrb_rating,
            background_image=game_data.background_image,
            playtime=game_data.playtime
        )

        db.add(new_game)
        db.commit()
        db.refresh(new_game)

        return new_game

    @staticmethod
    def get_game_by_id(db: Session, game_id: int) -> Optional[Game]:
        """
        Obtener un juego por su ID

        Args:
            db: Sesión de base de datos
            game_id: ID del juego

        Returns:
            Game o None si no existe
        """
        return db.query(Game).filter(Game.id == game_id).first()

    @staticmethod
    def get_games_paginated(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        platform: Optional[str] = None
    ) -> Tuple[List[Game], int]:
        """
        Obtener juegos con paginación y filtros opcionales

        Args:
            db: Sesión de base de datos
            page: Número de página (comienza en 1)
            page_size: Cantidad de juegos por página
            search: Búsqueda por nombre (opcional)
            genre: Filtrar por género (opcional)
            platform: Filtrar por plataforma (opcional)

        Returns:
            Tupla con (lista de juegos, total de juegos)
        """
        query = db.query(Game)

        # Aplicar filtro de búsqueda
        if search:
            query = query.filter(Game.name.ilike(f"%{search}%"))

        # Aplicar filtro de género (PostgreSQL JSON)
        if genre:
            query = query.filter(
                Game.genres_json.op('@>')(f'[{{"name": "{genre}"}}]')
            )

        # Aplicar filtro de plataforma (PostgreSQL JSON)
        if platform:
            query = query.filter(
                Game.parent_platforms_json.op('@>')(f'[{{"platform": {{"name": "{platform}"}}}}]')
            )

        # Contar total
        total = query.count()

        # Aplicar paginación
        offset = (page - 1) * page_size
        games = query.order_by(Game.name).offset(offset).limit(page_size).all()

        return games, total

    @staticmethod
    def update_game(
        db: Session,
        game_id: int,
        game_data: GameUpdateRequest
    ) -> Optional[Game]:
        """
        Actualizar un juego existente

        Args:
            db: Sesión de base de datos
            game_id: ID del juego a actualizar
            game_data: Datos a actualizar

        Returns:
            Game actualizado o None si no existe
        """
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return None

        # Actualizar solo los campos proporcionados
        update_data = game_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(game, field, value)

        game.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(game)

        return game

    @staticmethod
    def delete_game(db: Session, game_id: int) -> bool:
        """
        Eliminar un juego

        Args:
            db: Sesión de base de datos
            game_id: ID del juego a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            return False

        db.delete(game)
        db.commit()

        return True

    @staticmethod
    def get_game_stats(db: Session) -> dict:
        """
        Obtener estadísticas de los juegos

        Args:
            db: Sesión de base de datos

        Returns:
            Dict con estadísticas
        """
        total_games = db.query(func.count(Game.id)).scalar()

        # Contar géneros manualmente desde Python debido a complejidad de JSON en PostgreSQL
        games_with_genres = db.query(Game.genres_json).filter(Game.genres_json.isnot(None)).all()
        genre_counts = {}
        for (genres_json,) in games_with_genres:
            if genres_json:
                for genre in genres_json:
                    genre_name = genre.get('name', '')
                    if genre_name:
                        genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1

        # Top 10 géneros
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        genres_stats = [{"genre": g[0], "count": g[1]} for g in top_genres]

        # Contar plataformas manualmente
        games_with_platforms = db.query(Game.parent_platforms_json).filter(
            Game.parent_platforms_json.isnot(None)
        ).all()
        platform_counts = {}
        for (platforms_json,) in games_with_platforms:
            if platforms_json:
                for platform_obj in platforms_json:
                    platform_name = platform_obj.get('platform', {}).get('name', '')
                    if platform_name:
                        platform_counts[platform_name] = platform_counts.get(platform_name, 0) + 1

        platforms_stats = [{"platform": p[0], "count": p[1]} for p in platform_counts.items()]

        return {
            "total_games": total_games,
            "genres": genres_stats,
            "platforms": platforms_stats
        }

    @staticmethod
    def search_games(db: Session, query: str, limit: int = 10) -> List[Game]:
        """
        Buscar juegos por nombre

        Args:
            db: Sesión de base de datos
            query: Texto a buscar
            limit: Límite de resultados

        Returns:
            Lista de juegos encontrados
        """
        return db.query(Game)\
            .filter(Game.name.ilike(f"%{query}%"))\
            .order_by(Game.name)\
            .limit(limit)\
            .all()
