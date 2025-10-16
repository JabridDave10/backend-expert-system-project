from typing import List, Tuple, Dict, Any

from app.modules.expert_system.schemas.recommendation_request_dto import PreferenceRequest
from app.modules.expert_system.schemas.recommendation_response_dto import RecommendationItem


class ExpertEngine:
    """Motor de recomendaciones simple basado en reglas, sin librerías externas."""

    def __init__(self) -> None:
        # Dataset local mínimo de ejemplo. En producción, reemplazar por fuente real.
        self._catalog = [
            {
                "id": 1,
                "title": "Elden Ring",
                "genres": ["RPG", "Action"],
                "platforms": ["PC", "PS5", "Xbox"],
                "price": 59.99,
                "age_rating": 16,
                "playtime_hours": 80,
                "difficulty": "hard",
                "multiplayer": True,
                "rating": 4.8,
                "metacritic": 96,
                "released": "2022-02-25",
            },
            {
                "id": 2,
                "title": "Stardew Valley",
                "genres": ["Simulation", "RPG"],
                "platforms": ["PC", "Switch", "PS5"],
                "price": 14.99,
                "age_rating": 7,
                "playtime_hours": 60,
                "difficulty": "easy",
                "multiplayer": True,
                "rating": 4.5,
                "metacritic": 89,
                "released": "2016-02-26",
            },
            {
                "id": 3,
                "title": "Hades",
                "genres": ["Action", "Roguelike"],
                "platforms": ["PC", "Switch", "PS5"],
                "price": 24.99,
                "age_rating": 12,
                "playtime_hours": 25,
                "difficulty": "normal",
                "multiplayer": False,
                "rating": 4.6,
                "metacritic": 93,
                "released": "2020-09-17",
            },
            {
                "id": 4,
                "title": "The Witcher 3",
                "genres": ["RPG", "Adventure"],
                "platforms": ["PC", "PS5", "Xbox"],
                "price": 39.99,
                "age_rating": 18,
                "playtime_hours": 100,
                "difficulty": "normal",
                "multiplayer": False,
                "rating": 4.7,
                "metacritic": 92,
                "released": "2015-05-19",
            },
        ]

    def reload_from_cache(self, rawg_items: List[Dict[str, Any]]) -> None:
        """Reemplaza el catálogo interno con datos mapeados desde RAWG."""
        mapped: List[Dict[str, Any]] = []
        for item in rawg_items:
            mapped_item = self._map_rawg_game(item)
            if mapped_item:
                mapped.append(mapped_item)
        if mapped:
            self._catalog = mapped

    def _map_rawg_game(self, g: Dict[str, Any]) -> Dict[str, Any]:
        # Campos mínimos esperados: id, name, genres, platforms, playtime, esrb_rating, tags (opcional)
        try:
            game_id = g.get("id")
            title = g.get("name") or ""
            genres = [x.get("name") for x in (g.get("genres") or []) if x.get("name")]
            # platforms: RAWG usa 'platforms' con objetos {platform: {name}}
            platforms = []
            for p in (g.get("platforms") or []):
                plat = (p.get("platform") or {}).get("name")
                if plat:
                    platforms.append(plat)
            playtime_hours = int(g.get("playtime") or 0)
            released = g.get("released") or ""
            rating = float(g.get("rating") or 0.0)
            metacritic = int(g.get("metacritic") or 0) if g.get("metacritic") is not None else 0
            # ESRB a edad aproximada
            esrb = (g.get("esrb_rating") or {}).get("name") if g.get("esrb_rating") else None
            age_map = {
                "Everyone": 6,
                "Everyone 10+": 10,
                "Teen": 13,
                "Mature": 17,
                "Adults Only": 21,
            }
            age_rating = age_map.get(esrb, 12 if esrb else 12)
            # Multiplayer por tag si aparece
            tags = [t.get("name", "").lower() for t in (g.get("tags") or []) if t.get("name")]
            multiplayer = any("multiplayer" in t for t in tags)
            # RAWG no entrega precio ni dificultad: default razonable
            price = 0.0
            difficulty = "normal"
            return {
                "id": game_id,
                "title": title,
                "genres": genres,
                "platforms": platforms,
                "price": price,
                "age_rating": age_rating,
                "playtime_hours": playtime_hours,
                "difficulty": difficulty,
                "multiplayer": multiplayer,
                "released": released,
                "rating": rating,
                "metacritic": metacritic,
            }
        except Exception:
            return {}

    def recommend(self, preferences: PreferenceRequest, limit: int) -> Tuple[List[RecommendationItem], List[str]]:
        rules_applied: List[str] = []
        candidates = list(self._catalog)

        # Regla 1: excluir géneros
        if preferences.exclude_genres:
            before = len(candidates)
            candidates = [g for g in candidates if not any(eg.lower() in [x.lower() for x in g["genres"]] for eg in preferences.exclude_genres)]
            rules_applied.append(f"Excluidos géneros {preferences.exclude_genres} ({before}->{len(candidates)})")

        # Regla 2: excluir plataformas
        if preferences.exclude_platforms:
            before = len(candidates)
            candidates = [g for g in candidates if not any(ep.lower() in [x.lower() for x in g["platforms"]] for ep in preferences.exclude_platforms)]
            rules_applied.append(f"Excluidas plataformas {preferences.exclude_platforms} ({before}->{len(candidates)})")

        # Regla 3: filtro por precio máximo
        if preferences.max_price is not None:
            before = len(candidates)
            candidates = [g for g in candidates if g["price"] <= preferences.max_price]
            rules_applied.append(f"Precio <= {preferences.max_price} ({before}->{len(candidates)})")

        # Regla 4: filtro por edad máxima
        if preferences.age_rating_max is not None:
            before = len(candidates)
            candidates = [g for g in candidates if g["age_rating"] <= preferences.age_rating_max]
            rules_applied.append(f"Edad <= {preferences.age_rating_max} ({before}->{len(candidates)})")

        # Regla 5: filtro por multijugador
        if preferences.allow_multiplayer is not None:
            before = len(candidates)
            if preferences.allow_multiplayer:
                candidates = [g for g in candidates if g["multiplayer"]]
                rules_applied.append(f"Solo multijugador ({before}->{len(candidates)})")
            else:
                candidates = [g for g in candidates if not g["multiplayer"]]
                rules_applied.append(f"Solo single-player ({before}->{len(candidates)})")

        # Regla 6: filtro por horas mínimas
        if preferences.min_playtime_hours is not None:
            before = len(candidates)
            candidates = [g for g in candidates if g["playtime_hours"] >= preferences.min_playtime_hours]
            rules_applied.append(f"Horas >= {preferences.min_playtime_hours} ({before}->{len(candidates)})")

        # Puntaje por afinidad
        def score(game: dict) -> float:
            score_value = 0.0
            # Géneros preferidos
            if preferences.genres:
                common = len(set([g.lower() for g in game["genres"]]) & set([g.lower() for g in preferences.genres]))
                score_value += common * 3.0
            # Plataformas preferidas
            if preferences.platforms:
                common = len(set([p.lower() for p in game["platforms"]]) & set([p.lower() for p in preferences.platforms]))
                score_value += common * 1.5
            # Dificultad preferida
            if preferences.difficulty and preferences.difficulty.lower() == game["difficulty"].lower():
                score_value += 2.0
            # Precio bajo puntúa más
            score_value += max(0.0, 5.0 - (game["price"] / 20.0))
            # Más horas de juego, más puntaje (suavizado)
            score_value += min(5.0, game["playtime_hours"] / 20.0)
            # Calidad general por rating/metacritic
            score_value += (game.get("rating") or 0.0)  # 0-5 directamente
            score_value += (game.get("metacritic") or 0) / 20.0  # normalizado ~0-5
            return score_value

        # Ordenar por puntaje descendente
        ranked = sorted(candidates, key=score, reverse=True)

        items: List[RecommendationItem] = [
            RecommendationItem(
                id=g["id"],
                title=g["title"],
                genres=g["genres"],
                platforms=g["platforms"],
                price=g["price"],
                age_rating=g["age_rating"],
                playtime_hours=g["playtime_hours"],
                difficulty=g["difficulty"],
                multiplayer=g["multiplayer"],
                score=score(g),
            )
            for g in ranked[:limit]
        ]

        return items, rules_applied
