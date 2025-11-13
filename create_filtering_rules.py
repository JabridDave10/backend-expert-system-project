"""
Script para Crear Reglas de FILTRADO/DESCARTE

Este script genera reglas que ELIMINAN recomendaciones que no cumplen con los criterios del usuario.
Las reglas de filtrado se ejecutan DESPUÉS de las reglas de recomendación.

Tipos de filtros:
1. Edad (ESRB rating vs min_age)
2. Presupuesto (price vs budget_level)
3. Multijugador (multiplayer tags vs prefers_multiplayer)
4. Singleplayer (singleplayer tags vs prefers_singleplayer)
"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.core.database import SessionLocal
from app.modules.expert_system.services.rule_service import RuleService
from app.modules.expert_system.models.game import Game


def get_age_from_esrb(esrb: str) -> int:
    """Convierte ESRB a edad mínima"""
    age_map = {
        "Everyone": 0,
        "Everyone 10+": 10,
        "Teen": 13,
        "Mature": 17,
        "Adults Only": 18,
    }
    return age_map.get(esrb, 0)


def main():
    print("=" * 70)
    print("CREANDO REGLAS DE FILTRADO Y DESCARTE")
    print("=" * 70)

    db = SessionLocal()

    # Obtener todos los juegos de la BD
    games = db.query(Game).all()
    print(f"\n1️⃣  Juegos en base de datos: {len(games)}")

    rules_created = 0
    rules_skipped = 0

    print(f"\n2️⃣  Generando reglas de filtrado...")

    for game in games:
        game_id = game.id
        game_name = game.name
        game_esrb = game.esrb_rating or "Everyone"
        min_age_required = get_age_from_esrb(game_esrb)
        has_multiplayer = game.is_multiplayer()
        has_singleplayer = game.is_singleplayer()

        # Verificar plataformas disponibles
        has_pc = game.has_platform("PC")
        has_playstation = game.has_platform("PlayStation")
        has_nintendo = game.has_platform("Nintendo")
        has_xbox = game.has_platform("Xbox")

        # =================================================================
        # REGLA 1: Filtrar por EDAD - Si el usuario es menor, descartar juegos Mature
        # =================================================================
        if min_age_required >= 17:  # Juegos Mature/Adults Only
            try:
                RuleService.create_rule(
                    db=db,
                    name=f"FILTER-Age-Discard-{game_id}",
                    description=f"Descartar {game_name} si el usuario es menor de {min_age_required}",
                    conditions_json=[
                        {"entity": f"recommendation_{game_id}", "attribute": "game_id", "operator": "==", "value": game_id},
                        {"entity": "user", "attribute": "min_age", "operator": "<", "value": min_age_required},
                    ],
                    actions_json=[
                        {
                            "action": "retract_fact",
                            "entity": "recommendation",
                            "attribute": f"game_{game_id}",
                            "value": game_id,
                            "reason": f"{game_name} requiere edad {min_age_required}+ (ESRB: {game_esrb})"
                        }
                    ],
                    priority=50,  # Alta prioridad para filtros de seguridad
                    category="filter_age"
                )
                rules_created += 1
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"      ❌ Error: {e}")
                rules_skipped += 1

        # =================================================================
        # REGLA 2: Filtrar por MULTIPLAYER - Descartar si no es multijugador y el usuario lo quiere
        # =================================================================
        if not has_multiplayer:
            try:
                RuleService.create_rule(
                    db=db,
                    name=f"FILTER-NoMultiplayer-{game_id}",
                    description=f"Descartar {game_name} si el usuario quiere multijugador",
                    conditions_json=[
                        {"entity": f"recommendation_{game_id}", "attribute": "game_id", "operator": "==", "value": game_id},
                        {"entity": "user", "attribute": "prefers_multiplayer", "operator": "==", "value": True},
                    ],
                    actions_json=[
                        {
                            "action": "retract_fact",
                            "entity": "recommendation",
                            "attribute": f"game_{game_id}",
                            "value": game_id,
                            "reason": f"{game_name} no tiene multijugador"
                        }
                    ],
                    priority=40,
                    category="filter_multiplayer"
                )
                rules_created += 1
            except Exception:
                rules_skipped += 1

        # =================================================================
        # REGLA 3: Filtrar por SINGLEPLAYER - Descartar si no es singleplayer y el usuario lo quiere
        # =================================================================
        if not has_singleplayer:
            try:
                RuleService.create_rule(
                    db=db,
                    name=f"FILTER-NoSingleplayer-{game_id}",
                    description=f"Descartar {game_name} si el usuario quiere singleplayer",
                    conditions_json=[
                        {"entity": f"recommendation_{game_id}", "attribute": "game_id", "operator": "==", "value": game_id},
                        {"entity": "user", "attribute": "prefers_singleplayer", "operator": "==", "value": True},
                    ],
                    actions_json=[
                        {
                            "action": "retract_fact",
                            "entity": "recommendation",
                            "attribute": f"game_{game_id}",
                            "value": game_id,
                            "reason": f"{game_name} no tiene singleplayer"
                        }
                    ],
                    priority=40,
                    category="filter_singleplayer"
                )
                rules_created += 1
            except Exception:
                rules_skipped += 1

        # =================================================================
        # REGLA 4: Filtrar por PLATAFORMA PC
        # =================================================================
        if not has_pc:
            try:
                RuleService.create_rule(
                    db=db,
                    name=f"FILTER-NoPlatformPC-{game_id}",
                    description=f"Descartar {game_name} si el usuario quiere PC",
                    conditions_json=[
                        {"entity": f"recommendation_{game_id}", "attribute": "game_id", "operator": "==", "value": game_id},
                        {"entity": "user", "attribute": "prefers_platform", "operator": "==", "value": "PC"},
                    ],
                    actions_json=[
                        {
                            "action": "retract_fact",
                            "entity": "recommendation",
                            "attribute": f"game_{game_id}",
                            "value": game_id,
                            "reason": f"{game_name} no está disponible en PC"
                        }
                    ],
                    priority=40,
                    category="filter_platform"
                )
                rules_created += 1
            except Exception:
                rules_skipped += 1

        # =================================================================
        # REGLA 5: Filtrar por PLATAFORMA PlayStation
        # =================================================================
        if not has_playstation:
            try:
                RuleService.create_rule(
                    db=db,
                    name=f"FILTER-NoPlatformPlayStation-{game_id}",
                    description=f"Descartar {game_name} si el usuario quiere PlayStation",
                    conditions_json=[
                        {"entity": f"recommendation_{game_id}", "attribute": "game_id", "operator": "==", "value": game_id},
                        {"entity": "user", "attribute": "prefers_platform", "operator": "==", "value": "PlayStation"},
                    ],
                    actions_json=[
                        {
                            "action": "retract_fact",
                            "entity": "recommendation",
                            "attribute": f"game_{game_id}",
                            "value": game_id,
                            "reason": f"{game_name} no está disponible en PlayStation"
                        }
                    ],
                    priority=40,
                    category="filter_platform"
                )
                rules_created += 1
            except Exception:
                rules_skipped += 1

        # =================================================================
        # REGLA 6: Filtrar por PLATAFORMA Nintendo
        # =================================================================
        if not has_nintendo:
            try:
                RuleService.create_rule(
                    db=db,
                    name=f"FILTER-NoPlatformNintendo-{game_id}",
                    description=f"Descartar {game_name} si el usuario quiere Nintendo",
                    conditions_json=[
                        {"entity": f"recommendation_{game_id}", "attribute": "game_id", "operator": "==", "value": game_id},
                        {"entity": "user", "attribute": "prefers_platform", "operator": "==", "value": "Nintendo"},
                    ],
                    actions_json=[
                        {
                            "action": "retract_fact",
                            "entity": "recommendation",
                            "attribute": f"game_{game_id}",
                            "value": game_id,
                            "reason": f"{game_name} no está disponible en Nintendo"
                        }
                    ],
                    priority=40,
                    category="filter_platform"
                )
                rules_created += 1
            except Exception:
                rules_skipped += 1

        # =================================================================
        # REGLA 7: Filtrar por PLATAFORMA Xbox
        # =================================================================
        if not has_xbox:
            try:
                RuleService.create_rule(
                    db=db,
                    name=f"FILTER-NoPlatformXbox-{game_id}",
                    description=f"Descartar {game_name} si el usuario quiere Xbox",
                    conditions_json=[
                        {"entity": f"recommendation_{game_id}", "attribute": "game_id", "operator": "==", "value": game_id},
                        {"entity": "user", "attribute": "prefers_platform", "operator": "==", "value": "Xbox"},
                    ],
                    actions_json=[
                        {
                            "action": "retract_fact",
                            "entity": "recommendation",
                            "attribute": f"game_{game_id}",
                            "value": game_id,
                            "reason": f"{game_name} no está disponible en Xbox"
                        }
                    ],
                    priority=40,
                    category="filter_platform"
                )
                rules_created += 1
            except Exception:
                rules_skipped += 1

    db.commit()
    db.close()

    print(f"\n✅ Proceso completado:")
    print(f"   - Reglas de filtrado creadas: {rules_created}")
    print(f"   - Reglas saltadas (ya existían): {rules_skipped}")

    # Mostrar estadísticas finales
    db = SessionLocal()
    from app.modules.expert_system.models import Rule
    from collections import Counter

    all_rules = db.query(Rule).all()
    categories = Counter([r.category for r in all_rules])

    print(f"\n📊 Base de conocimiento completa:")
    print(f"   - Total reglas: {len(all_rules)}")
    print(f"\n   Por categoría:")
    for cat, count in categories.most_common():
        print(f"     • {cat}: {count} reglas")

    db.close()


if __name__ == "__main__":
    main()
