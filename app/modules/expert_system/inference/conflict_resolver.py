"""
Conflict Resolver - Resolución de Conflictos para el Sistema Experto

Cuando múltiples reglas son aplicables simultáneamente, el Conflict Resolver
decide cuál regla debe dispararse primero.

Estrategias implementadas:
1. Prioridad/Salience: Reglas con mayor prioridad primero
2. Especificidad: Reglas más específicas (más condiciones) primero
3. Recencia: Reglas más recientemente creadas primero
4. Combinación: Combina las anteriores
"""

from typing import List, Tuple, Optional
from enum import Enum
from app.modules.expert_system.models.rule import Rule
from app.modules.expert_system.models.fact import Fact


class ConflictResolutionStrategy(Enum):
    """Estrategias de resolución de conflictos"""
    PRIORITY = "priority"  # Mayor prioridad primero
    SPECIFICITY = "specificity"  # Más específica primero
    RECENCY = "recency"  # Más reciente primero
    COMBINED = "combined"  # Combinación de prioridad + especificidad + recencia


class ConflictResolver:
    """
    Resuelve conflictos entre reglas aplicables usando diferentes estrategias.

    Ejemplo:
        resolver = ConflictResolver(strategy=ConflictResolutionStrategy.COMBINED)
        selected_rule = resolver.resolve(applicable_rules)
    """

    def __init__(self, strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.COMBINED):
        """
        Inicializa el conflict resolver.

        Args:
            strategy: Estrategia de resolución a usar
        """
        self.strategy = strategy

    def resolve(self, applicable_rules: List[Tuple[Rule, List[Fact]]]) -> Optional[Tuple[Rule, List[Fact]]]:
        """
        Selecciona la mejor regla de entre las aplicables.

        Args:
            applicable_rules: Lista de tuplas (rule, facts_used)

        Returns:
            Tupla (rule, facts_used) seleccionada, o None si no hay reglas
        """
        if not applicable_rules:
            return None

        if len(applicable_rules) == 1:
            return applicable_rules[0]

        # Aplicar estrategia de resolución
        if self.strategy == ConflictResolutionStrategy.PRIORITY:
            return self._resolve_by_priority(applicable_rules)

        elif self.strategy == ConflictResolutionStrategy.SPECIFICITY:
            return self._resolve_by_specificity(applicable_rules)

        elif self.strategy == ConflictResolutionStrategy.RECENCY:
            return self._resolve_by_recency(applicable_rules)

        elif self.strategy == ConflictResolutionStrategy.COMBINED:
            return self._resolve_combined(applicable_rules)

        else:
            # Default: prioridad
            return self._resolve_by_priority(applicable_rules)

    def _resolve_by_priority(self, applicable_rules: List[Tuple[Rule, List[Fact]]]) -> Tuple[Rule, List[Fact]]:
        """
        Resuelve por prioridad: regla con mayor priority gana.

        Args:
            applicable_rules: Reglas aplicables

        Returns:
            Regla seleccionada
        """
        return max(applicable_rules, key=lambda x: x[0].priority)

    def _resolve_by_specificity(self, applicable_rules: List[Tuple[Rule, List[Fact]]]) -> Tuple[Rule, List[Fact]]:
        """
        Resuelve por especificidad: regla con más condiciones gana.

        Args:
            applicable_rules: Reglas aplicables

        Returns:
            Regla seleccionada
        """
        return max(applicable_rules, key=lambda x: x[0].specificity)

    def _resolve_by_recency(self, applicable_rules: List[Tuple[Rule, List[Fact]]]) -> Tuple[Rule, List[Fact]]:
        """
        Resuelve por recencia: regla más recientemente creada gana.

        Args:
            applicable_rules: Reglas aplicables

        Returns:
            Regla seleccionada
        """
        return max(applicable_rules, key=lambda x: x[0].id)

    def _resolve_combined(self, applicable_rules: List[Tuple[Rule, List[Fact]]]) -> Tuple[Rule, List[Fact]]:
        """
        Resuelve usando estrategia combinada:
        1. Mayor prioridad
        2. Si hay empate, más específica
        3. Si hay empate, más reciente

        Args:
            applicable_rules: Reglas aplicables

        Returns:
            Regla seleccionada
        """
        # Ordenar por: prioridad (desc), especificidad (desc), id (desc)
        sorted_rules = sorted(
            applicable_rules,
            key=lambda x: (
                x[0].priority,  # Mayor prioridad primero
                x[0].specificity,  # Más específica primero
                x[0].id  # Más reciente primero
            ),
            reverse=True
        )

        return sorted_rules[0]

    def get_sorted_rules(self, applicable_rules: List[Tuple[Rule, List[Fact]]]) -> List[Tuple[Rule, List[Fact]]]:
        """
        Retorna todas las reglas aplicables ordenadas según la estrategia.

        Útil para ver el orden completo de priorización.

        Args:
            applicable_rules: Reglas aplicables

        Returns:
            Lista ordenada de reglas
        """
        if not applicable_rules:
            return []

        if self.strategy == ConflictResolutionStrategy.PRIORITY:
            return sorted(applicable_rules, key=lambda x: x[0].priority, reverse=True)

        elif self.strategy == ConflictResolutionStrategy.SPECIFICITY:
            return sorted(applicable_rules, key=lambda x: x[0].specificity, reverse=True)

        elif self.strategy == ConflictResolutionStrategy.RECENCY:
            return sorted(applicable_rules, key=lambda x: x[0].id, reverse=True)

        elif self.strategy == ConflictResolutionStrategy.COMBINED:
            return sorted(
                applicable_rules,
                key=lambda x: (x[0].priority, x[0].specificity, x[0].id),
                reverse=True
            )

        else:
            return applicable_rules

    def explain_selection(self, selected_rule: Rule, applicable_rules: List[Tuple[Rule, List[Fact]]]) -> str:
        """
        Genera una explicación de por qué se seleccionó una regla.

        Args:
            selected_rule: Regla seleccionada
            applicable_rules: Todas las reglas aplicables

        Returns:
            Texto explicativo
        """
        if len(applicable_rules) == 1:
            return f"Rule '{selected_rule.name}' was the only applicable rule."

        explanation_parts = [
            f"Rule '{selected_rule.name}' was selected from {len(applicable_rules)} applicable rules.",
            f"Strategy: {self.strategy.value}",
        ]

        if self.strategy == ConflictResolutionStrategy.PRIORITY:
            explanation_parts.append(f"Selected because it has the highest priority ({selected_rule.priority}).")

        elif self.strategy == ConflictResolutionStrategy.SPECIFICITY:
            explanation_parts.append(f"Selected because it has the most conditions ({selected_rule.specificity}).")

        elif self.strategy == ConflictResolutionStrategy.RECENCY:
            explanation_parts.append(f"Selected because it is the most recently created (ID: {selected_rule.id}).")

        elif self.strategy == ConflictResolutionStrategy.COMBINED:
            explanation_parts.append(
                f"Selected using combined strategy: "
                f"priority={selected_rule.priority}, "
                f"specificity={selected_rule.specificity}, "
                f"recency_id={selected_rule.id}"
            )

        # Mostrar comparación con otras reglas
        other_rules = [r for r, _ in applicable_rules if r.id != selected_rule.id]
        if other_rules:
            explanation_parts.append("\nOther applicable rules:")
            for rule in other_rules[:3]:  # Mostrar solo las primeras 3
                explanation_parts.append(
                    f"  - '{rule.name}': priority={rule.priority}, "
                    f"specificity={rule.specificity}, id={rule.id}"
                )

        return "\n".join(explanation_parts)

    def set_strategy(self, strategy: ConflictResolutionStrategy):
        """Cambia la estrategia de resolución."""
        self.strategy = strategy

    def __repr__(self):
        return f"<ConflictResolver(strategy={self.strategy.value})>"
