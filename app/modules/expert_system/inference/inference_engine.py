"""
Inference Engine - Motor de Inferencia del Sistema Experto

Implementa el algoritmo de Forward Chaining (razonamiento hacia adelante):
1. Parte de hechos iniciales
2. Busca reglas aplicables
3. Resuelve conflictos entre reglas
4. Dispara la regla seleccionada
5. Agrega nuevos hechos inferidos
6. Repite hasta alcanzar conclusión o máximo de iteraciones

Este es el componente central del sistema experto.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from app.modules.expert_system.models.rule import Rule
from app.modules.expert_system.models.fact import Fact
from app.modules.expert_system.inference.working_memory import WorkingMemory
from app.modules.expert_system.inference.pattern_matcher import PatternMatcher
from app.modules.expert_system.inference.conflict_resolver import (
    ConflictResolver,
    ConflictResolutionStrategy,
)


class InferenceResult:
    """Resultado de una sesión de inferencia"""

    def __init__(self):
        self.success: bool = False
        self.iterations: int = 0
        self.rules_fired: List[Dict[str, Any]] = []
        self.final_facts: List[Fact] = []
        self.conclusions: List[Dict[str, Any]] = []
        self.error_message: Optional[str] = None
        self.execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "iterations": self.iterations,
            "rules_fired_count": len(self.rules_fired),
            "rules_fired": self.rules_fired,
            "final_facts_count": len(self.final_facts),
            "final_facts": [f.to_dict() for f in self.final_facts],
            "conclusions": self.conclusions,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
        }


class InferenceEngine:
    """
    Motor de inferencia que implementa Forward Chaining.

    Ejemplo de uso:
        engine = InferenceEngine(rules, initial_facts)
        result = engine.forward_chaining(max_iterations=100)
        print(f"Iterations: {result.iterations}")
        print(f"Rules fired: {len(result.rules_fired)}")
        print(f"Conclusions: {result.conclusions}")
    """

    def __init__(
        self,
        rules: List[Rule],
        initial_facts: List[Fact],
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.COMBINED,
    ):
        """
        Inicializa el motor de inferencia.

        Args:
            rules: Lista de reglas de la base de conocimiento
            initial_facts: Hechos iniciales (entrada del usuario)
            conflict_strategy: Estrategia de resolución de conflictos
        """
        self.rules = rules
        self.working_memory = WorkingMemory(initial_facts)
        self.pattern_matcher = PatternMatcher(self.working_memory)
        self.conflict_resolver = ConflictResolver(conflict_strategy)

        # Tracking
        self.fired_rules: List[Dict[str, Any]] = []
        self.iteration_count = 0

    def forward_chaining(
        self,
        max_iterations: int = 100,
        goal: Optional[str] = None,
    ) -> InferenceResult:
        """
        Ejecuta el algoritmo de Forward Chaining.

        Args:
            max_iterations: Número máximo de iteraciones
            goal: Objetivo opcional (ej: "recommend_game")

        Returns:
            InferenceResult con el resultado de la inferencia
        """
        result = InferenceResult()
        start_time = datetime.now()

        try:
            print(f"🚀 Starting forward chaining (max_iterations={max_iterations})")
            print(f"   Initial facts: {self.working_memory.count()}")
            print(f"   Available rules: {len(self.rules)}")

            # Iterar hasta alcanzar conclusión o máximo de iteraciones
            for iteration in range(1, max_iterations + 1):
                self.iteration_count = iteration

                # PASO 1: Pattern Matching - Encontrar reglas aplicables
                applicable_rules = self.pattern_matcher.find_matching_rules(self.rules)

                if not applicable_rules:
                    print(f"   Iteration {iteration}: No applicable rules found. Stopping.")
                    break

                print(f"   Iteration {iteration}: {len(applicable_rules)} applicable rules")

                # PASO 2: Conflict Resolution - Seleccionar mejor regla
                selected = self.conflict_resolver.resolve(applicable_rules)

                if not selected:
                    print(f"   Iteration {iteration}: Conflict resolution failed. Stopping.")
                    break

                rule, facts_used = selected
                print(f"   Iteration {iteration}: Selected rule '{rule.name}' (priority={rule.priority})")

                # PASO 3: Fire Rule - Ejecutar la regla
                new_facts = self.fire_rule(rule, facts_used, iteration)

                if not new_facts:
                    print(f"   Iteration {iteration}: Rule '{rule.name}' produced no new facts. Stopping.")
                    break

                print(f"   Iteration {iteration}: Added {len(new_facts)} new facts")

                # Verificar si alcanzamos el objetivo
                if goal and self.check_goal_reached(goal):
                    print(f"   Iteration {iteration}: Goal '{goal}' reached!")
                    break

            # Generar resultado
            result.success = True
            result.iterations = self.iteration_count
            result.rules_fired = self.fired_rules
            result.final_facts = self.working_memory.get_all_facts()
            result.conclusions = self.extract_conclusions()

            end_time = datetime.now()
            result.execution_time = (end_time - start_time).total_seconds()

            print(f"✅ Forward chaining completed in {result.iterations} iterations")
            print(f"   Rules fired: {len(result.rules_fired)}")
            print(f"   Final facts: {len(result.final_facts)}")
            print(f"   Execution time: {result.execution_time:.3f}s")

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            print(f"❌ Error during inference: {e}")
            import traceback
            traceback.print_exc()

        return result

    def fire_rule(
        self,
        rule: Rule,
        facts_used: List[Fact],
        iteration: int,
    ) -> List[Fact]:
        """
        Dispara una regla: ejecuta sus acciones y genera nuevos hechos.

        Args:
            rule: Regla a disparar
            facts_used: Hechos que cumplieron las condiciones
            iteration: Número de iteración actual

        Returns:
            Lista de nuevos hechos generados
        """
        new_facts = []

        # Ejecutar cada acción de la regla
        for action in rule.actions_json:
            action_type = action.get("action")

            if action_type == "add_fact":
                # Crear nuevo hecho
                fact = Fact(
                    entity=action.get("entity"),
                    attribute=action.get("attribute"),
                    value=str(action.get("value")),
                    value_type=action.get("value_type", "string"),
                    confidence=action.get("confidence", 1.0),
                    source="inferred",
                    is_temporary=True,
                )
                new_facts.append(fact)
                self.working_memory.add_fact(fact)

            elif action_type == "recommend":
                # Crear recomendación (como hecho especial)
                game_id = action.get("game_id")
                confidence = action.get("confidence", 1.0)
                reason = action.get("reason", "")

                fact = Fact(
                    entity="recommendation",
                    attribute=f"game_{game_id}",
                    value=str(confidence),
                    value_type="float",
                    confidence=confidence,
                    source="inferred",
                    is_temporary=True,
                )
                new_facts.append(fact)
                self.working_memory.add_fact(fact)

            elif action_type == "set_conclusion":
                # Establecer conclusión
                conclusion_type = action.get("conclusion_type", "result")
                value = action.get("value")

                fact = Fact(
                    entity="conclusion",
                    attribute=conclusion_type,
                    value=str(value),
                    value_type="string",
                    confidence=action.get("confidence", 1.0),
                    source="inferred",
                    is_temporary=True,
                )
                new_facts.append(fact)
                self.working_memory.add_fact(fact)

        # Registrar regla disparada
        self.fired_rules.append({
            "iteration": iteration,
            "rule_id": rule.id,
            "rule_name": rule.name,
            "rule_priority": rule.priority,
            "facts_matched": [f.to_dict() for f in facts_used],
            "facts_added": [f.to_dict() for f in new_facts],
        })

        return new_facts

    def check_goal_reached(self, goal: str) -> bool:
        """
        Verifica si se alcanzó el objetivo.

        Args:
            goal: Objetivo a verificar (ej: "recommend_game")

        Returns:
            True si se alcanzó, False si no
        """
        if goal == "recommend_game":
            # Verificar si hay al menos una recomendación
            return self.working_memory.fact_exists("recommendation", "game_1") or \
                   self.working_memory.fact_exists("recommendation", "game_2") or \
                   self.working_memory.fact_exists("recommendation", "game_3") or \
                   self.working_memory.fact_exists("recommendation", "game_4")

        elif goal == "diagnose":
            # Verificar si hay conclusión
            return self.working_memory.fact_exists("conclusion", "result")

        else:
            # Objetivo genérico
            return self.working_memory.fact_exists("goal", goal)

    def extract_conclusions(self) -> List[Dict[str, Any]]:
        """
        Extrae las conclusiones de la memoria de trabajo.

        Returns:
            Lista de conclusiones
        """
        conclusions = []

        # Buscar hechos de tipo "recommendation"
        for fact in self.working_memory.get_facts_by_entity("recommendation"):
            if fact.attribute.startswith("game_"):
                game_id = fact.attribute.replace("game_", "")
                conclusions.append({
                    "type": "recommendation",
                    "game_id": int(game_id),
                    "confidence": fact.confidence,
                })

        # Buscar hechos de tipo "conclusion"
        for fact in self.working_memory.get_facts_by_entity("conclusion"):
            conclusions.append({
                "type": "conclusion",
                "attribute": fact.attribute,
                "value": fact.get_typed_value(),
                "confidence": fact.confidence,
            })

        return conclusions

    def get_rules_fired_summary(self) -> List[str]:
        """
        Retorna un resumen de las reglas disparadas.

        Returns:
            Lista de strings con resumen
        """
        summary = []
        for fired in self.fired_rules:
            summary.append(
                f"Iter {fired['iteration']}: {fired['rule_name']} "
                f"(matched {len(fired['facts_matched'])} facts, "
                f"added {len(fired['facts_added'])} facts)"
            )
        return summary

    def reset(self, new_initial_facts: Optional[List[Fact]] = None):
        """
        Reinicia el motor de inferencia.

        Args:
            new_initial_facts: Nuevos hechos iniciales opcionales
        """
        if new_initial_facts:
            self.working_memory = WorkingMemory(new_initial_facts)
            self.pattern_matcher = PatternMatcher(self.working_memory)
        else:
            self.working_memory.clear()

        self.fired_rules.clear()
        self.iteration_count = 0

    def __repr__(self):
        return (
            f"<InferenceEngine("
            f"rules={len(self.rules)}, "
            f"facts={self.working_memory.count()}, "
            f"iteration={self.iteration_count})>"
        )
