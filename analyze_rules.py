from app.core.database import SessionLocal
from app.modules.expert_system.models.rule import Rule
import json

db = SessionLocal()

# Get all rules
rules = db.query(Rule).all()
print(f'Total rules: {len(rules)}')

# Analyze genres
genres = {}
for r in rules:
    conds = r.conditions_json
    for c in conds:
        if c.get('attribute') == 'prefers_genre':
            g = c.get('value')
            genres[g] = genres.get(g, 0) + 1

print('\nReglas por género:')
for g, count in sorted(genres.items(), key=lambda x: -x[1]):
    print(f'  {g}: {count} reglas')

# Show sample rules for RPG
print('\nEjemplos de reglas RPG:')
rpg_rules = [r for r in rules if any(c.get('attribute') == 'prefers_genre' and c.get('value') == 'RPG' for c in r.conditions_json)][:5]
for r in rpg_rules:
    print(f'\n  Rule: {r.name}')
    print(f'  Conditions: {json.dumps(r.conditions_json, indent=4)}')
    print(f'  Actions: {json.dumps(r.actions_json, indent=4)[:200]}...')

db.close()
