"""
Script Avanzado para Generar Reglas Complejas del Sistema Experto

Este script genera reglas que consideran TODOS los filtros del wizard:
- Género (prefers_genre)
- Calidad (wants_quality)
- Multijugador (prefers_multiplayer / prefers_singleplayer)
- Edad (min_age) - Alineado con el frontend
- Presupuesto (budget_level) - Alineado con el frontend

Genera combinaciones inteligentes de condiciones para recomendaciones precisas.
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.core.database import SessionLocal
from app.modules.expert_system.services.rule_service import RuleService


def load_catalog_games(ndjson_path: str):
    """Carga todos los juegos del catálogo NDJSON"""
    games = []
    with open(ndjson_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                game = json.loads(line)
                games.append(game)
    return games


def get_age_requirement(esrb_rating: str) -> int:
    """Convierte ESRB rating a edad mínima requerida"""
    age_map = {
        "Everyone": 0,
        "Everyone 10+": 10,
        "Teen": 13,
        "Mature": 17,
        "Adults Only": 18,
    }
    return age_map.get(esrb_rating, 0)


def get_budget_category(price: float) -> str:
    """Categoriza el precio en niveles de presupuesto"""
    if price == 0:
        return "free"
    elif price < 10:
        return "low"
    elif price < 30:
        return "medium"
    else:
        return "high"


def is_multiplayer(game: dict) -> bool:
    """Determina si el juego tiene multijugador"""
    tags = [t.get("name", "").lower() if isinstance(t, dict) else str(t).lower() for t in game.get("tags", [])]
    return any(tag in tags for tag in ["multiplayer", "co-op", "pvp", "online co-op", "mmo"])


def is_singleplayer(game: dict) -> bool:
    """Determina si el juego tiene singleplayer"""
    tags = [t.get("name", "").lower() if isinstance(t, dict) else str(t).lower() for t in game.get("tags", [])]
    return any(tag in tags for tag in ["single-player", "singleplayer", "single player"])


def main():
    print("=" * 70)
    print("GENERANDO REGLAS AVANZADAS CON TODOS LOS FILTROS")
    print("=" * 70)

    # Cargar catálogo
    catalog_path = root_dir / "app_data" / "catalog_games.ndjson"
    print(f"\n1️⃣  Cargando catálogo: {catalog_path}")
    games = load_catalog_games(str(catalog_path))
    print(f"   ✅ {len(games)} juegos cargados")

    # Filtrar juegos de calidad
    quality_games = [g for g in games if g.get("rating", 0) >= 3.5]
    print(f"\n2️⃣  Juegos de calidad (rating >= 3.5): {len(quality_games)}")

    # Agrupar por género
    games_by_genre = defaultdict(list)
    for game in quality_games:
        for genre_obj in game.get("genres", []):
            genre_name = genre_obj.get("name") if isinstance(genre_obj, dict) else str(genre_obj)
            if genre_name:
                games_by_genre[genre_name].append(game)

    print(f"\n3️⃣  Géneros encontrados: {len(games_by_genre)}")
    for genre, games_list in sorted(games_by_genre.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        print(f"   - {genre}: {len(games_list)} juegos")

    # Conectar a la base de datos
    db = SessionLocal()
    rules_created = 0
    rules_skipped = 0

    print(f"\n4️⃣  Generando reglas avanzadas...")

    # Para cada género, tomar los mejores juegos
    for genre, genre_games in games_by_genre.items():
        # Ordenar por rating
        genre_games.sort(key=lambda x: x.get("rating", 0), reverse=True)

        # Tomar hasta 30 juegos por género
        top_games = genre_games[:30]

        for i, game in enumerate(top_games):
            game_id = game["id"]
            game_name = game["name"]
            game_rating = game["rating"]
            game_metacritic = game.get("metacritic", 0)
            game_price = game.get("price", 0)
            game_esrb = game.get("age", "Everyone")
            min_age_required = get_age_requirement(game_esrb)
            budget_cat = get_budget_category(game_price)
            has_multiplayer = is_multiplayer(game)
            has_singleplayer = is_singleplayer(game)

            priority_base = 30 - i  # Mayor prioridad para mejores juegos

            # =================================================================
            # REGLA 1: Género + Calidad + Edad + Presupuesto + Multiplayer
            # =================================================================
            if game_rating >= 4.0 and has_multiplayer:
                conditions = [
                    {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": genre},
                    {"entity": "user", "attribute": "wants_quality", "operator": "==", "value": True},
                    {"entity": "user", "attribute": "min_age", "operator": ">=", "value": min_age_required},
                    {"entity": "user", "attribute": "budget_level", "operator": "==", "value": budget_cat},
                    {"entity": "user", "attribute": "prefers_multiplayer", "operator": "==", "value": True},
                ]

                try:
                    RuleService.create_rule(
                        db=db,
                        name=f"ADV-{genre}-QualityMulti-{budget_cat}-{game_id}",
                        description=f"Recomendar {game_name} para {genre} + calidad + multiplayer + presupuesto {budget_cat}",
                        conditions_json=conditions,
                        actions_json=[{
                            "action": "recommend",
                            "game_id": game_id,
                            "confidence": min(0.98, game_rating / 5.0 + 0.1),
                            "reason": f"{game_name} es un excelente {genre} multijugador (rating {game_rating:.1f})"
                        }],
                        priority=priority_base + 10,
                        category="advanced_recommendation"
                    )
                    rules_created += 1
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"      ❌ Error: {e}")
                    rules_skipped += 1

            # =================================================================
            # REGLA 2: Género + Calidad + Edad + Singleplayer
            # =================================================================
            if game_rating >= 4.0 and has_singleplayer:
                conditions = [
                    {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": genre},
                    {"entity": "user", "attribute": "wants_quality", "operator": "==", "value": True},
                    {"entity": "user", "attribute": "min_age", "operator": ">=", "value": min_age_required},
                    {"entity": "user", "attribute": "prefers_singleplayer", "operator": "==", "value": True},
                ]

                try:
                    RuleService.create_rule(
                        db=db,
                        name=f"ADV-{genre}-QualitySingle-{game_id}",
                        description=f"Recomendar {game_name} para {genre} + calidad + singleplayer",
                        conditions_json=conditions,
                        actions_json=[{
                            "action": "recommend",
                            "game_id": game_id,
                            "confidence": min(0.97, game_rating / 5.0 + 0.08),
                            "reason": f"{game_name} es un excelente {genre} para jugar solo (rating {game_rating:.1f})"
                        }],
                        priority=priority_base + 9,
                        category="advanced_recommendation"
                    )
                    rules_created += 1
                except Exception:
                    rules_skipped += 1

            # =================================================================
            # REGLA 3: Género + Calidad + Edad + Presupuesto
            # =================================================================
            if game_rating >= 3.8:
                conditions = [
                    {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": genre},
                    {"entity": "user", "attribute": "wants_quality", "operator": "==", "value": True},
                    {"entity": "user", "attribute": "min_age", "operator": ">=", "value": min_age_required},
                    {"entity": "user", "attribute": "budget_level", "operator": "==", "value": budget_cat},
                ]

                try:
                    RuleService.create_rule(
                        db=db,
                        name=f"ADV-{genre}-QualityBudget-{budget_cat}-{game_id}",
                        description=f"Recomendar {game_name} para {genre} + calidad + presupuesto {budget_cat}",
                        conditions_json=conditions,
                        actions_json=[{
                            "action": "recommend",
                            "game_id": game_id,
                            "confidence": min(0.95, game_rating / 5.0 + 0.05),
                            "reason": f"{game_name} ({genre}) tiene excelente relación calidad/precio ({budget_cat})"
                        }],
                        priority=priority_base + 7,
                        category="advanced_recommendation"
                    )
                    rules_created += 1
                except Exception:
                    rules_skipped += 1

            # =================================================================
            # REGLA 4: Género + Edad + Presupuesto (sin filtro calidad)
            # =================================================================
            conditions = [
                {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": genre},
                {"entity": "user", "attribute": "min_age", "operator": ">=", "value": min_age_required},
                {"entity": "user", "attribute": "budget_level", "operator": "==", "value": budget_cat},
            ]

            try:
                RuleService.create_rule(
                    db=db,
                    name=f"ADV-{genre}-AgeBudget-{budget_cat}-{game_id}",
                    description=f"Recomendar {game_name} para {genre} + edad {min_age_required}+ + presupuesto {budget_cat}",
                    conditions_json=conditions,
                    actions_json=[{
                        "action": "recommend",
                        "game_id": game_id,
                        "confidence": min(0.88, game_rating / 5.0),
                        "reason": f"{game_name} es un buen {genre} dentro de tu presupuesto ({budget_cat})"
                    }],
                    priority=priority_base + 3,
                    category="advanced_recommendation"
                )
                rules_created += 1
            except Exception:
                rules_skipped += 1

            # =================================================================
            # REGLA 5: Género + Multiplayer (sin otros filtros)
            # =================================================================
            if has_multiplayer:
                conditions = [
                    {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": genre},
                    {"entity": "user", "attribute": "prefers_multiplayer", "operator": "==", "value": True},
                ]

                try:
                    RuleService.create_rule(
                        db=db,
                        name=f"ADV-{genre}-Multi-{game_id}",
                        description=f"Recomendar {game_name} para {genre} + multiplayer",
                        conditions_json=conditions,
                        actions_json=[{
                            "action": "recommend",
                            "game_id": game_id,
                            "confidence": min(0.85, game_rating / 5.0),
                            "reason": f"{game_name} es un {genre} multijugador divertido"
                        }],
                        priority=priority_base + 2,
                        category="advanced_recommendation"
                    )
                    rules_created += 1
                except Exception:
                    rules_skipped += 1

            # =================================================================
            # REGLA 6: Presupuesto FREE + Calidad (juegos gratis de calidad)
            # =================================================================
            if budget_cat == "free" and game_rating >= 3.8:
                conditions = [
                    {"entity": "user", "attribute": "budget_level", "operator": "==", "value": "free"},
                    {"entity": "user", "attribute": "wants_quality", "operator": "==", "value": True},
                    {"entity": "user", "attribute": "min_age", "operator": ">=", "value": min_age_required},
                ]

                try:
                    RuleService.create_rule(
                        db=db,
                        name=f"ADV-Free-Quality-{game_id}",
                        description=f"Recomendar {game_name} - juego gratis de calidad",
                        conditions_json=conditions,
                        actions_json=[{
                            "action": "recommend",
                            "game_id": game_id,
                            "confidence": min(0.96, game_rating / 5.0 + 0.08),
                            "reason": f"{game_name} es GRATIS y tiene excelente calidad (rating {game_rating:.1f})"
                        }],
                        priority=priority_base + 15,  # Alta prioridad para free+quality
                        category="advanced_recommendation"
                    )
                    rules_created += 1
                except Exception:
                    rules_skipped += 1

    db.commit()
    db.close()

    print(f"\n✅ Proceso completado:")
    print(f"   - Reglas creadas: {rules_created}")
    print(f"   - Reglas saltadas (ya existían): {rules_skipped}")
    print(f"   - Total: {rules_created + rules_skipped}")

    # Mostrar estadísticas finales
    db = SessionLocal()
    from app.modules.expert_system.models import Rule
    total_rules = db.query(Rule).count()
    advanced_rules = db.query(Rule).filter(Rule.category == "advanced_recommendation").count()
    db.close()

    print(f"\n📊 Base de conocimiento:")
    print(f"   - Total reglas en BD: {total_rules}")
    print(f"   - Reglas avanzadas: {advanced_rules}")
    print(f"   - Reglas básicas: {total_rules - advanced_rules}")


if __name__ == "__main__":
    main()
