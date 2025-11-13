"""
Script para Generar Reglas Automáticamente desde el Catálogo de Juegos

Lee el archivo catalog_games.ndjson y crea reglas inteligentes basadas en:
- Géneros de juegos
- Ratings y metacritic
- Tags (multiplayer, singleplayer, etc.)
- ESRB ratings (edad)
- Plataformas

Uso:
    python populate_rules_from_catalog.py
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Agregar el directorio raíz al path
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

    print(f"📚 Loaded {len(games)} games from catalog")
    return games


def analyze_catalog(games):
    """Analiza el catálogo para encontrar juegos representativos"""

    # Mapeo de ESRB a edad
    age_map = {
        "Everyone": 6,
        "Everyone 10+": 10,
        "Teen": 13,
        "Mature": 17,
        "Adults Only": 21,
    }

    analysis = {
        "by_genre": defaultdict(list),
        "by_tag": defaultdict(list),
        "by_esrb": defaultdict(list),
        "high_rated": [],
        "multiplayer": [],
        "singleplayer": [],
    }

    for game in games:
        game_id = game.get("id")
        name = game.get("name")
        rating = float(game.get("rating") or 0)
        metacritic = int(game.get("metacritic") or 0) if game.get("metacritic") else 0

        # Analizar géneros
        genres = game.get("genres") or []
        for genre in genres:
            genre_name = genre.get("name") if isinstance(genre, dict) else str(genre)
            analysis["by_genre"][genre_name].append({
                "id": game_id,
                "name": name,
                "rating": rating,
                "metacritic": metacritic,
            })

        # Analizar ESRB
        esrb = game.get("esrb_rating")
        if esrb:
            esrb_name = esrb.get("name") if isinstance(esrb, dict) else str(esrb)
            age = age_map.get(esrb_name, 12)
            analysis["by_esrb"][esrb_name].append({
                "id": game_id,
                "name": name,
                "age": age,
                "rating": rating,
            })

        # Analizar tags
        tags = game.get("tags") or []
        tag_names = [t.get("name", "").lower() if isinstance(t, dict) else str(t).lower() for t in tags]

        for tag in tag_names:
            if any(keyword in tag for keyword in ["multiplayer", "co-op", "pvp", "competitive"]):
                analysis["multiplayer"].append({
                    "id": game_id,
                    "name": name,
                    "rating": rating,
                })

            if any(keyword in tag for keyword in ["singleplayer", "single-player", "single player"]):
                analysis["singleplayer"].append({
                    "id": game_id,
                    "name": name,
                    "rating": rating,
                })

        # Juegos con alto rating
        if rating >= 4.0 and metacritic >= 80:
            analysis["high_rated"].append({
                "id": game_id,
                "name": name,
                "rating": rating,
                "metacritic": metacritic,
            })

    # Ordenar listas por rating
    for key in analysis:
        if isinstance(analysis[key], list):
            analysis[key].sort(key=lambda x: x.get("rating", 0), reverse=True)
        elif isinstance(analysis[key], dict):
            for subkey in analysis[key]:
                analysis[key][subkey].sort(key=lambda x: x.get("rating", 0), reverse=True)

    return analysis


def generate_rules_from_analysis(analysis):
    """Genera reglas basadas en el análisis del catálogo"""

    rules = []
    rule_names_seen = set()  # Prevenir duplicados

    def add_rule(rule):
        """Agrega una regla solo si no existe el nombre"""
        if rule["name"] not in rule_names_seen:
            rules.append(rule)
            rule_names_seen.add(rule["name"])

    # ========================================
    # REGLAS COMPLEJAS POR GÉNERO + EDAD
    # ========================================

    top_genres = ["Action", "RPG", "Adventure", "Strategy", "Shooter", "Indie", "Simulation", "Puzzle", "Platformer"]

    for genre in top_genres:
        if genre in analysis["by_genre"] and analysis["by_genre"][genre]:
            # Tomar TODOS los juegos con rating >= 3.5 (en vez de solo top 5)
            all_genre_games = analysis["by_genre"][genre]
            top_games = [g for g in all_genre_games if g["rating"] >= 3.5][:50]  # Max 50 por género

            for i, game in enumerate(top_games):
                game_id = game["id"]
                game_name = game["name"]
                game_rating = game["rating"]
                game_metacritic = game["metacritic"]

                priority_base = 12 - i

                # REGLA 1: Género + Alta Calidad (rating alto)
                if game_rating >= 4.0:
                    add_rule({
                        "name": f"RPG-{genre}-Quality-{game_id}",  # ID único
                        "description": f"Recomendar {game_name} para usuarios de {genre} que buscan calidad (rating: {game_rating})",
                        "conditions": [
                            {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": genre},
                            {"entity": "user", "attribute": "wants_quality", "operator": "==", "value": True},
                        ],
                        "actions": [
                            {
                                "action": "recommend",
                                "game_id": game_id,
                                "confidence": min(0.96, game_rating / 5.0),
                                "reason": f"{game_name} es un excelente {genre} con rating {game_rating} y metacritic {game_metacritic}"
                            }
                        ],
                        "priority": priority_base + 2,
                        "category": "recommendation",
                    })

                # REGLA 2: Género básico (fallback)
                add_rule({
                    "name": f"RPG-{genre}-Basic-{game_id}",
                    "description": f"Recomendar {game_name} para fans de {genre}",
                    "conditions": [
                        {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": genre},
                    ],
                    "actions": [
                        {
                            "action": "recommend",
                            "game_id": game_id,
                            "confidence": min(0.88, game_rating / 5.0),
                            "reason": f"{game_name} es un gran juego de {genre}"
                        }
                    ],
                    "priority": priority_base - 2,
                    "category": "recommendation",
                })

    # ========================================
    # REGLAS COMPLEJAS POR EDAD + GÉNERO
    # ========================================

    # Juegos para menores (Everyone, Everyone 10+, Teen)
    safe_ratings = ["Everyone", "Everyone 10+", "Teen"]
    safe_games = []

    for rating in safe_ratings:
        if rating in analysis["by_esrb"]:
            safe_games.extend(analysis["by_esrb"][rating][:3])

    if safe_games:
        safe_games.sort(key=lambda x: x.get("rating", 0), reverse=True)

        for i, game in enumerate(safe_games[:5]):
            # REGLA: Edad + Calidad para menores
            add_rule({
                "name": f"Safe-Age-Quality-{game['id']}",
                "description": f"Para menores que buscan calidad, recomendar {game['name']}",
                "conditions": [
                    {"entity": "user", "attribute": "age", "operator": "<", "value": 18},
                    {"entity": "user", "attribute": "wants_quality", "operator": "==", "value": True},
                ],
                "actions": [
                    {
                        "action": "recommend",
                        "game_id": game["id"],
                        "confidence": 0.93,
                        "reason": f"{game['name']} es apropiado para menores y tiene excelente rating"
                    }
                ],
                "priority": 18 - i,  # Muy alta prioridad para seguridad
                "category": "safety",
            })

            # REGLA: Solo edad (fallback)
            add_rule({
                "name": f"Safe-Age-Basic-{game['id']}",
                "description": f"Para menores, recomendar {game['name']}",
                "conditions": [
                    {"entity": "user", "attribute": "age", "operator": "<", "value": 18},
                ],
                "actions": [
                    {
                        "action": "recommend",
                        "game_id": game["id"],
                        "confidence": 0.85,
                        "reason": f"{game['name']} es apropiado para menores (edad {game['age']}+)"
                    }
                ],
                "priority": 15 - i,
                "category": "safety",
            })

    # Juegos para adultos (Mature) + Combinaciones
    if "Mature" in analysis["by_esrb"] and analysis["by_esrb"]["Mature"]:
        mature_games = analysis["by_esrb"]["Mature"][:5]

        for i, game in enumerate(mature_games):
            # REGLA: Adulto + Alta Calidad
            if game["rating"] >= 4.0:
                add_rule({
                    "name": f"Mature-Quality-{game['id']}",
                    "description": f"Para adultos que buscan calidad, recomendar {game['name']}",
                    "conditions": [
                        {"entity": "user", "attribute": "age", "operator": ">=", "value": 18},
                        {"entity": "user", "attribute": "wants_quality", "operator": "==", "value": True},
                    ],
                    "actions": [
                        {
                            "action": "recommend",
                            "game_id": game["id"],
                            "confidence": min(0.95, game["rating"] / 5.0),
                            "reason": f"{game['name']} es un juego maduro de alta calidad (rating: {game['rating']})"
                        }
                    ],
                    "priority": 13 - i,
                    "category": "recommendation",
                })

            # REGLA: Solo adulto (fallback)
            add_rule({
                "name": f"Mature-Basic-{game['id']}",
                "description": f"Para adultos, recomendar {game['name']}",
                "conditions": [
                    {"entity": "user", "attribute": "age", "operator": ">=", "value": 18},
                ],
                "actions": [
                    {
                        "action": "recommend",
                        "game_id": game["id"],
                        "confidence": min(0.88, game["rating"] / 5.0),
                        "reason": f"{game['name']} es un juego maduro entretenido"
                    }
                ],
                "priority": 10 - i,
                "category": "recommendation",
            })

    # ========================================
    # REGLAS COMPLEJAS POR MULTIJUGADOR
    # ========================================

    if analysis["multiplayer"]:
        top_multiplayer = analysis["multiplayer"][:5]

        for i, game in enumerate(top_multiplayer):
            game_id = game["id"]
            game_name = game["name"]
            game_rating = game["rating"]

            # REGLA: Multijugador + Alta Calidad
            if game_rating >= 4.0:
                add_rule({
                    "name": f"Multiplayer-Quality-{game_id}",
                    "description": f"Para jugadores multijugador que buscan calidad, recomendar {game_name}",
                    "conditions": [
                        {"entity": "user", "attribute": "prefers_multiplayer", "operator": "==", "value": True},
                        {"entity": "user", "attribute": "wants_quality", "operator": "==", "value": True},
                    ],
                    "actions": [
                        {
                            "action": "recommend",
                            "game_id": game_id,
                            "confidence": min(0.94, game_rating / 5.0),
                            "reason": f"{game_name} ofrece una experiencia multijugador de calidad excepcional"
                        }
                    ],
                    "priority": 12 - i,
                    "category": "recommendation",
                })

            # REGLA: Multijugador + Edad adulta
            add_rule({
                "name": f"Multiplayer-Adult-{game_id}",
                "description": f"Para adultos que buscan multijugador, recomendar {game_name}",
                "conditions": [
                    {"entity": "user", "attribute": "prefers_multiplayer", "operator": "==", "value": True},
                    {"entity": "user", "attribute": "age", "operator": ">=", "value": 18},
                ],
                "actions": [
                    {
                        "action": "recommend",
                        "game_id": game_id,
                        "confidence": 0.89 - (i * 0.03),
                        "reason": f"{game_name} es ideal para adultos que disfrutan del multijugador"
                    }
                ],
                "priority": 10 - i,
                "category": "recommendation",
            })

            # REGLA: Solo multijugador (fallback)
            add_rule({
                "name": f"Multiplayer-Basic-{game_id}",
                "description": f"Para jugadores multijugador, recomendar {game_name}",
                "conditions": [
                    {"entity": "user", "attribute": "prefers_multiplayer", "operator": "==", "value": True},
                ],
                "actions": [
                    {
                        "action": "recommend",
                        "game_id": game_id,
                        "confidence": 0.84 - (i * 0.04),
                        "reason": f"{game_name} ofrece una buena experiencia multijugador"
                    }
                ],
                "priority": 8 - i,
                "category": "recommendation",
            })

    # ========================================
    # REGLAS COMPLEJAS POR SINGLEPLAYER
    # ========================================

    if analysis["singleplayer"]:
        top_singleplayer = analysis["singleplayer"][:5]

        for i, game in enumerate(top_singleplayer):
            game_id = game["id"]
            game_name = game["name"]
            game_rating = game["rating"]

            # REGLA: Singleplayer + Alta Calidad
            if game_rating >= 4.0:
                add_rule({
                    "name": f"Singleplayer-Quality-{game_id}",
                    "description": f"Para jugadores solitarios que buscan calidad, recomendar {game_name}",
                    "conditions": [
                        {"entity": "user", "attribute": "prefers_multiplayer", "operator": "==", "value": False},
                        {"entity": "user", "attribute": "wants_quality", "operator": "==", "value": True},
                    ],
                    "actions": [
                        {
                            "action": "recommend",
                            "game_id": game_id,
                            "confidence": min(0.93, game_rating / 5.0),
                            "reason": f"{game_name} es perfecto para jugar solo con excelente calidad"
                        }
                    ],
                    "priority": 11 - i,
                    "category": "recommendation",
                })

            # REGLA: Singleplayer + Tiempo limitado
            add_rule({
                "name": f"Singleplayer-Limited-Time-{game_id}",
                "description": f"Para jugadores con poco tiempo que prefieren singleplayer, recomendar {game_name}",
                "conditions": [
                    {"entity": "user", "attribute": "prefers_multiplayer", "operator": "==", "value": False},
                    {"entity": "user", "attribute": "available_hours_per_week", "operator": "<", "value": 10},
                ],
                "actions": [
                    {
                        "action": "recommend",
                        "game_id": game_id,
                        "confidence": 0.86,
                        "reason": f"{game_name} es ideal para sesiones cortas en solitario"
                    }
                ],
                "priority": 9 - i,
                "category": "recommendation",
            })

            # REGLA: Solo singleplayer (fallback)
            add_rule({
                "name": f"Singleplayer-Basic-{game_id}",
                "description": f"Para jugadores solitarios, recomendar {game_name}",
                "conditions": [
                    {"entity": "user", "attribute": "prefers_multiplayer", "operator": "==", "value": False},
                ],
                "actions": [
                    {
                        "action": "recommend",
                        "game_id": game_id,
                        "confidence": 0.83 - (i * 0.03),
                        "reason": f"{game_name} es perfecto para disfrutar en solitario"
                    }
                ],
                "priority": 7 - i,
                "category": "recommendation",
            })

    # ========================================
    # REGLAS DE ALTA CALIDAD GENERAL
    # ========================================

    if analysis["high_rated"]:
        top_rated = analysis["high_rated"][:10]

        for i, game in enumerate(top_rated):
            game_id = game["id"]
            game_name = game["name"]
            game_rating = game["rating"]
            game_metacritic = game["metacritic"]

            # REGLA: Solo calidad (fallback general)
            add_rule({
                "name": f"Quality-General-{game_id}",
                "description": f"Para usuarios que buscan calidad sin preferencias específicas, recomendar {game_name}",
                "conditions": [
                    {"entity": "user", "attribute": "wants_quality", "operator": "==", "value": True},
                ],
                "actions": [
                    {
                        "action": "recommend",
                        "game_id": game_id,
                        "confidence": min(0.95, (game_rating / 5.0 + game_metacritic / 100.0) / 2),
                        "reason": f"{game_name} tiene críticas excepcionales (rating: {game_rating}, metacritic: {game_metacritic})"
                    }
                ],
                "priority": 6 - (i // 2),  # Desciende gradualmente
                "category": "quality",
            })

    # ========================================
    # REGLAS DE FILTRADO Y RESTRICCIONES
    # ========================================

    # Filtro de presupuesto bajo
    add_rule({
        "name": "Filter-Budget-Low",
        "description": "Aplicar filtro de precio bajo cuando el presupuesto es limitado",
        "conditions": [
            {"entity": "user", "attribute": "max_budget", "operator": "<=", "value": 20},
        ],
        "actions": [
            {
                "action": "add_fact",
                "entity": "filter",
                "attribute": "max_price",
                "value": "20",
                "value_type": "float",
                "confidence": 1.0
            }
        ],
        "priority": 20,  # Muy alta prioridad
        "category": "filtering",
    })

    # Filtro de presupuesto medio
    add_rule({
        "name": "Filter-Budget-Medium",
        "description": "Aplicar filtro de precio medio para presupuesto moderado",
        "conditions": [
            {"entity": "user", "attribute": "max_budget", "operator": "<=", "value": 40},
            {"entity": "user", "attribute": "max_budget", "operator": ">", "value": 20},
        ],
        "actions": [
            {
                "action": "add_fact",
                "entity": "filter",
                "attribute": "max_price",
                "value": "40",
                "value_type": "float",
                "confidence": 1.0
            }
        ],
        "priority": 19,
        "category": "filtering",
    })

    # Filtro de plataforma PC
    add_rule({
        "name": "Filter-Platform-PC",
        "description": "Filtrar por plataforma PC",
        "conditions": [
            {"entity": "user", "attribute": "platform", "operator": "==", "value": "PC"},
        ],
        "actions": [
            {
                "action": "add_fact",
                "entity": "filter",
                "attribute": "required_platform",
                "value": "PC",
                "value_type": "string",
                "confidence": 1.0
            }
        ],
        "priority": 16,
        "category": "filtering",
    })

    # Filtro de plataforma consola
    add_rule({
        "name": "Filter-Platform-PlayStation",
        "description": "Filtrar por plataforma PlayStation",
        "conditions": [
            {"entity": "user", "attribute": "platform", "operator": "==", "value": "PlayStation"},
        ],
        "actions": [
            {
                "action": "add_fact",
                "entity": "filter",
                "attribute": "required_platform",
                "value": "PlayStation",
                "value_type": "string",
                "confidence": 1.0
            }
        ],
        "priority": 16,
        "category": "filtering",
    })

    # Filtro de tiempo limitado
    add_rule({
        "name": "Filter-Time-Limited",
        "description": "Para usuarios con poco tiempo, agregar preferencia por juegos cortos",
        "conditions": [
            {"entity": "user", "attribute": "available_hours_per_week", "operator": "<", "value": 10},
        ],
        "actions": [
            {
                "action": "add_fact",
                "entity": "preference",
                "attribute": "prefer_short_games",
                "value": "true",
                "value_type": "bool",
                "confidence": 0.9
            }
        ],
        "priority": 14,
        "category": "filtering",
    })

    return rules


def main():
    print("=" * 70)
    print("GENERANDO REGLAS DESDE EL CATÁLOGO DE JUEGOS")
    print("=" * 70)
    print()

    # Ruta al catálogo
    ndjson_path = "app_data/catalog_games.ndjson"

    if not Path(ndjson_path).exists():
        print(f"❌ Error: No se encontró el archivo {ndjson_path}")
        print("   Asegúrate de que el catálogo existe antes de ejecutar este script.")
        sys.exit(1)

    try:
        # 1. Cargar catálogo
        print("1️⃣  Cargando catálogo de juegos...")
        games = load_catalog_games(ndjson_path)

        # 2. Analizar catálogo
        print("\n2️⃣  Analizando juegos...")
        analysis = analyze_catalog(games)

        print(f"   - Géneros encontrados: {len(analysis['by_genre'])}")
        print(f"   - Juegos con alto rating: {len(analysis['high_rated'])}")
        print(f"   - Juegos multijugador: {len(analysis['multiplayer'])}")
        print(f"   - Juegos singleplayer: {len(analysis['singleplayer'])}")

        # Mostrar top géneros
        print("\n   Top géneros por cantidad de juegos:")
        top_genres = sorted(analysis["by_genre"].items(), key=lambda x: len(x[1]), reverse=True)[:10]
        for genre, games_list in top_genres:
            print(f"     - {genre}: {len(games_list)} juegos")

        # 3. Generar reglas
        print("\n3️⃣  Generando reglas inteligentes...")
        rules = generate_rules_from_analysis(analysis)
        print(f"   ✅ {len(rules)} reglas generadas")

        # 4. Guardar reglas en BD
        print("\n4️⃣  Guardando reglas en la base de datos...")
        db = SessionLocal()

        try:
            # Obtener reglas existentes
            existing_rules = RuleService.get_all_rules(db, active_only=False, limit=10000)
            existing_rule_names = {rule.name for rule in existing_rules}

            created_count = 0
            skipped_count = 0

            for rule_data in rules:
                if rule_data["name"] in existing_rule_names:
                    skipped_count += 1
                    continue

                try:
                    rule = RuleService.create_rule(
                        db=db,
                        name=rule_data["name"],
                        description=rule_data["description"],
                        conditions_json=rule_data["conditions"],
                        actions_json=rule_data["actions"],
                        priority=rule_data["priority"],
                        category=rule_data["category"],
                    )

                    created_count += 1

                    if created_count <= 5:  # Mostrar solo las primeras 5
                        print(f"   ✅ '{rule.name}' (prioridad: {rule.priority})")

                except Exception as e:
                    print(f"   ❌ Error creando '{rule_data['name']}': {e}")

            if created_count > 5:
                print(f"   ... y {created_count - 5} reglas más")

            print()
            print(f"✅ Proceso completado:")
            print(f"   - Reglas creadas: {created_count}")
            print(f"   - Reglas saltadas: {skipped_count} (ya existían)")
            print(f"   - Total en BD: {len(RuleService.get_all_rules(db, active_only=False, limit=10000))}")
            print()

        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("=" * 70)


if __name__ == "__main__":
    main()
