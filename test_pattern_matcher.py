"""Test para ver si el Pattern Matcher encuentra las reglas de filtrado"""

from app.core.database import SessionLocal
from app.modules.expert_system.models import Rule, Fact
from app.modules.expert_system.inference.working_memory import WorkingMemory
from app.modules.expert_system.inference.pattern_matcher import PatternMatcher

db = SessionLocal()

# Cargar una regla de filtrado específica
filter_rule = db.query(Rule).filter(Rule.name == 'FILTER-NoMultiplayer-58781').first()

print(f"✅ Regla: {filter_rule.name}")
print(f"   Condiciones: {filter_rule.conditions_json}")

# Crear working memory con los hechos necesarios
wm = WorkingMemory()

# Agregar los hechos que deberían hacer match
fact1 = Fact(
    entity="recommendation_58781",
    attribute="game_id",
    value="58781",
    value_type="integer",
    confidence=1.0,
    source="test",
    is_temporary=True
)

fact2 = Fact(
    entity="user",
    attribute="prefers_multiplayer",
    value="True",  # Note: stored as string
    value_type="boolean",
    confidence=1.0,
    source="test",
    is_temporary=True
)

wm.add_fact(fact1)
wm.add_fact(fact2)

print(f"\n✅ Working Memory:")
print(f"   - recommendation_58781.game_id = {wm.get_fact('recommendation_58781', 'game_id').value}")
print(f"   - user.prefers_multiplayer = {wm.get_fact('user', 'prefers_multiplayer').value}")

# Crear pattern matcher
pm = PatternMatcher(wm)

# Intentar hacer match
matched, facts_used = pm.match_rule(filter_rule)

print(f"\n{'✅' if matched else '❌'} Pattern Match Result: {matched}")
if facts_used:
    print(f"   Facts used: {[(f.entity, f.attribute, f.value) for f in facts_used]}")

# Probar cada condición individualmente
print(f"\n🔍 Testing conditions individually:")
for i, condition in enumerate(filter_rule.conditions_json):
    result, fact = pm.evaluate_condition(condition)
    print(f"   Condition {i+1}: {condition}")
    print(f"   Result: {result}, Fact: {fact.entity if fact else 'None'}.{fact.attribute if fact else 'None'} = {fact.value if fact else 'None'}")

db.close()
