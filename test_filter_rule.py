from app.core.database import SessionLocal
from app.modules.expert_system.models import Rule
import json

db = SessionLocal()

rule = db.query(Rule).filter(Rule.name == 'FILTER-NoMultiplayer-58781').first()

if rule:
    print(f"✅ Regla existe: {rule.name}")
    print(f"\nCondiciones:")
    print(json.dumps(rule.conditions_json, indent=2))
    print(f"\nAcciones:")
    print(json.dumps(rule.actions_json, indent=2))
    print(f"\nPrioridad: {rule.priority}")
    print(f"Categoría: {rule.category}")
    print(f"Activa: {rule.is_active}")
else:
    print("❌ Regla NO existe")

db.close()
