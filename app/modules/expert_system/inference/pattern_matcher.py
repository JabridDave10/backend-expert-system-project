"""
Pattern Matcher - Emparejamiento de Patrones para el Sistema Experto

El Pattern Matcher evalúa si las condiciones de una regla se cumplen
con los hechos actuales en la memoria de trabajo.

Implementa un algoritmo simple de pattern matching (no RETE).
"""

from typing import List, Dict, Any, Optional
from app.modules.expert_system.models.rule import Rule
from app.modules.expert_system.models.fact import Fact
from app.modules.expert_system.inference.working_memory import WorkingMemory


class PatternMatcher:
    """
    Evaluador de condiciones para reglas del sistema experto.

    Soporta operadores:
    - Comparación: ==, !=, <, <=, >, >=
    - Pertenencia: in, not_in
    - Lógicos: and, or, not
    - Existencia: exists, not_exists
    """

    def __init__(self, working_memory: WorkingMemory):
        """
        Inicializa el pattern matcher.

        Args:
            working_memory: Memoria de trabajo con los hechos actuales
        """
        self.working_memory = working_memory

    def match_rule(self, rule: Rule) -> tuple[bool, List[Fact]]:
        """
        Evalúa si una regla cumple con los hechos actuales.

        Args:
            rule: Regla a evaluar

        Returns:
            Tupla (matched, facts_used) donde:
            - matched: True si todas las condiciones se cumplen
            - facts_used: Lista de hechos que cumplieron las condiciones
        """
        if not rule.is_active:
            return False, []

        conditions = rule.conditions_json
        if not conditions or not isinstance(conditions, list):
            return False, []

        facts_used = []

        # Evaluar cada condición
        for condition in conditions:
            result, fact = self.evaluate_condition(condition)
            if not result:
                return False, []  # Una condición falló

            if fact:
                facts_used.append(fact)

        # Todas las condiciones se cumplieron
        return True, facts_used

    def evaluate_condition(self, condition: Dict[str, Any]) -> tuple[bool, Optional[Fact]]:
        """
        Evalúa una condición individual.

        Formato de condición:
        {
            "entity": "user_1",
            "attribute": "age",
            "operator": ">=",
            "value": 18
        }

        Args:
            condition: Diccionario con la condición

        Returns:
            Tupla (result, fact) donde:
            - result: True si la condición se cumple
            - fact: Hecho usado para evaluar la condición
        """
        entity = condition.get("entity")
        attribute = condition.get("attribute")
        operator = condition.get("operator", "==")
        expected_value = condition.get("value")

        if not entity or not attribute:
            return False, None

        # Obtener el hecho de la memoria de trabajo
        fact = self.working_memory.get_fact(entity, attribute)

        # Si el operador es "not_exists", invertimos la lógica
        if operator == "not_exists":
            return fact is None, None

        # Para otros operadores, el hecho debe existir
        if not fact:
            return False, None

        # Obtener el valor tipificado del hecho
        actual_value = fact.get_typed_value()

        # Evaluar según el operador
        result = self.apply_operator(actual_value, operator, expected_value)

        return result, fact

    def apply_operator(self, actual: Any, operator: str, expected: Any) -> bool:
        """
        Aplica un operador de comparación.

        Operadores soportados:
        - ==, !=, <, <=, >, >=
        - in, not_in
        - contains, not_contains
        - exists, not_exists

        Args:
            actual: Valor actual del hecho
            operator: Operador a aplicar
            expected: Valor esperado

        Returns:
            True si la operación se cumple, False si no
        """
        try:
            if operator == "==":
                return actual == expected

            elif operator == "!=":
                return actual != expected

            elif operator == "<":
                return float(actual) < float(expected)

            elif operator == "<=":
                return float(actual) <= float(expected)

            elif operator == ">":
                return float(actual) > float(expected)

            elif operator == ">=":
                return float(actual) >= float(expected)

            elif operator == "in":
                # Verifica si actual está en la lista expected
                if isinstance(expected, list):
                    return actual in expected
                # Verifica si actual es substring de expected
                return str(actual) in str(expected)

            elif operator == "not_in":
                if isinstance(expected, list):
                    return actual not in expected
                return str(actual) not in str(expected)

            elif operator == "contains":
                # Verifica si expected está en actual (lista o string)
                if isinstance(actual, list):
                    return expected in actual
                return str(expected) in str(actual)

            elif operator == "not_contains":
                if isinstance(actual, list):
                    return expected not in actual
                return str(expected) not in str(actual)

            elif operator == "exists":
                return actual is not None

            elif operator == "not_exists":
                return actual is None

            elif operator == "starts_with":
                return str(actual).startswith(str(expected))

            elif operator == "ends_with":
                return str(actual).endswith(str(expected))

            else:
                # Operador desconocido, retornar False
                print(f"Warning: Unknown operator '{operator}'")
                return False

        except (ValueError, TypeError, AttributeError) as e:
            # Error al evaluar, retornar False
            print(f"Error evaluating condition: {e}")
            return False

    def find_matching_rules(self, rules: List[Rule]) -> List[tuple[Rule, List[Fact]]]:
        """
        Encuentra todas las reglas que cumplen con los hechos actuales.

        Args:
            rules: Lista de reglas a evaluar

        Returns:
            Lista de tuplas (rule, facts_used) de reglas que cumplen
        """
        matching_rules = []

        for rule in rules:
            matched, facts_used = self.match_rule(rule)
            if matched:
                matching_rules.append((rule, facts_used))

        return matching_rules

    def match_rules_by_category(self, rules: List[Rule], category: str) -> List[tuple[Rule, List[Fact]]]:
        """
        Encuentra reglas que cumplen, filtradas por categoría.

        Args:
            rules: Lista de reglas
            category: Categoría a filtrar

        Returns:
            Lista de tuplas (rule, facts_used)
        """
        filtered_rules = [r for r in rules if r.category == category]
        return self.find_matching_rules(filtered_rules)

    def __repr__(self):
        return f"<PatternMatcher(working_memory={self.working_memory})>"
