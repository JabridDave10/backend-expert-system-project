"""
Script para Poblar Reglas Iniciales del Sistema Experto

Crea reglas de ejemplo para el sistema de recomendación de juegos.

Uso:
    python populate_rules.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from app.core.database import SessionLocal
from app.modules.expert_system.services.rule_service import RuleService


def create_sample_rules():
    """Crea reglas de ejemplo para el sistema experto"""

    rules = [
        # Regla 1: Recomendación de RPG para adultos
        {
            "name": "Recomendar RPG para adultos amantes de desafíos",
            "description": "Si el usuario es mayor de edad, le gustan los RPG y busca desafíos, recomendar Elden Ring",
            "conditions": [
                {"entity": "user", "attribute": "age", "operator": ">=", "value": 18},
                {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": "RPG"},
                {"entity": "user", "attribute": "prefers_difficulty", "operator": "==", "value": "hard"},
            ],
            "actions": [
                {
                    "action": "recommend",
                    "game_id": 1,
                    "confidence": 0.95,
                    "reason": "Elden Ring es un RPG desafiante perfecto para adultos que buscan retos"
                }
            ],
            "priority": 10,
            "category": "recommendation",
        },

        # Regla 2: Recomendación de juego casual
        {
            "name": "Recomendar juego casual y relajante",
            "description": "Si el usuario busca algo fácil y relajante, recomendar Stardew Valley",
            "conditions": [
                {"entity": "user", "attribute": "prefers_difficulty", "operator": "==", "value": "easy"},
                {"entity": "user", "attribute": "prefers_playtime", "operator": ">", "value": 30},
            ],
            "actions": [
                {
                    "action": "recommend",
                    "game_id": 2,
                    "confidence": 0.90,
                    "reason": "Stardew Valley es perfecto para juego relajado con mucho contenido"
                }
            ],
            "priority": 8,
            "category": "recommendation",
        },

        # Regla 3: Recomendación de acción y roguelike
        {
            "name": "Recomendar roguelike de acción",
            "description": "Si le gustan los juegos de acción con dificultad media, recomendar Hades",
            "conditions": [
                {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": "Action"},
                {"entity": "user", "attribute": "prefers_difficulty", "operator": "==", "value": "normal"},
            ],
            "actions": [
                {
                    "action": "recommend",
                    "game_id": 3,
                    "confidence": 0.88,
                    "reason": "Hades combina acción trepidante con dificultad equilibrada"
                }
            ],
            "priority": 9,
            "category": "recommendation",
        },

        # Regla 4: Recomendación de RPG narrativo
        {
            "name": "Recomendar RPG con historia profunda",
            "description": "Si es adulto y le gustan las historias inmersivas, recomendar The Witcher 3",
            "conditions": [
                {"entity": "user", "attribute": "age", "operator": ">=", "value": 18},
                {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": "RPG"},
                {"entity": "user", "attribute": "likes_story", "operator": "==", "value": True},
            ],
            "actions": [
                {
                    "action": "recommend",
                    "game_id": 4,
                    "confidence": 0.92,
                    "reason": "The Witcher 3 ofrece una de las mejores narrativas en RPGs"
                }
            ],
            "priority": 10,
            "category": "recommendation",
        },

        # Regla 5: Filtro de presupuesto bajo
        {
            "name": "Filtrar por presupuesto limitado",
            "description": "Si el usuario tiene presupuesto bajo, recomendar juegos económicos",
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
            "priority": 15,
            "category": "filtering",
        },

        # Regla 6: Preferencia por multijugador
        {
            "name": "Preferencia por juegos multijugador",
            "description": "Si el usuario prefiere multijugador, agregar filtro correspondiente",
            "conditions": [
                {"entity": "user", "attribute": "prefers_multiplayer", "operator": "==", "value": True},
            ],
            "actions": [
                {
                    "action": "add_fact",
                    "entity": "filter",
                    "attribute": "multiplayer_required",
                    "value": "true",
                    "value_type": "bool",
                    "confidence": 1.0
                }
            ],
            "priority": 12,
            "category": "filtering",
        },

        # Regla 7: Tiempo limitado
        {
            "name": "Recomendar juegos cortos para tiempo limitado",
            "description": "Si el usuario tiene poco tiempo, evitar juegos muy largos",
            "conditions": [
                {"entity": "user", "attribute": "available_hours_per_week", "operator": "<", "value": 10},
            ],
            "actions": [
                {
                    "action": "add_fact",
                    "entity": "filter",
                    "attribute": "max_playtime",
                    "value": "40",
                    "value_type": "int",
                    "confidence": 0.9
                }
            ],
            "priority": 8,
            "category": "filtering",
        },

        # Regla 8: Usuario joven - filtro de edad
        {
            "name": "Filtrar contenido apropiado para menores",
            "description": "Si el usuario es menor de 18, filtrar juegos para adultos",
            "conditions": [
                {"entity": "user", "attribute": "age", "operator": "<", "value": 18},
            ],
            "actions": [
                {
                    "action": "add_fact",
                    "entity": "filter",
                    "attribute": "max_age_rating",
                    "value": "13",
                    "value_type": "int",
                    "confidence": 1.0
                }
            ],
            "priority": 20,  # Prioridad alta para filtros de seguridad
            "category": "safety",
        },

        # Regla 9: Plataforma preferida
        {
            "name": "Filtrar por plataforma PC",
            "description": "Si el usuario solo tiene PC, filtrar por esa plataforma",
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
            "priority": 15,
            "category": "filtering",
        },

        # Regla 10: Recomendación genérica de alto rating
        {
            "name": "Recomendar juegos con alto rating cuando no hay preferencias claras",
            "description": "Si no se dispararon otras reglas, recomendar juegos con mejor valoración",
            "conditions": [
                {"entity": "user", "attribute": "no_clear_preferences", "operator": "==", "value": True},
            ],
            "actions": [
                {
                    "action": "add_fact",
                    "entity": "filter",
                    "attribute": "min_rating",
                    "value": "4.5",
                    "value_type": "float",
                    "confidence": 0.7
                }
            ],
            "priority": 1,  # Baja prioridad (regla catch-all)
            "category": "default",
        },
    ]

    return rules


def main():
    print("=" * 70)
    print("POBLANDO REGLAS INICIALES DEL SISTEMA EXPERTO")
    print("=" * 70)
    print()

    db = SessionLocal()

    try:
        # Obtener reglas existentes
        existing_rules = RuleService.get_all_rules(db, active_only=False, limit=1000)
        existing_rule_names = {rule.name for rule in existing_rules}

        print(f"Reglas existentes: {len(existing_rules)}")
        print()

        # Crear reglas de ejemplo
        sample_rules = create_sample_rules()
        created_count = 0
        skipped_count = 0

        for rule_data in sample_rules:
            if rule_data["name"] in existing_rule_names:
                print(f"⏭️  Saltando '{rule_data['name']}' (ya existe)")
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

                print(f"✅ Creada '{rule.name}' (prioridad: {rule.priority}, categoría: {rule.category})")
                created_count += 1

            except Exception as e:
                print(f"❌ Error creando '{rule_data['name']}': {e}")

        print()
        print(f"✅ Proceso completado:")
        print(f"   - Reglas creadas: {created_count}")
        print(f"   - Reglas saltadas: {skipped_count}")
        print(f"   - Total en BD: {len(RuleService.get_all_rules(db, active_only=False, limit=1000))}")
        print()

    except Exception as e:
        print(f"❌ Error durante la población de reglas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()

    print("=" * 70)


if __name__ == "__main__":
    main()
