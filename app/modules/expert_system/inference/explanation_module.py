"""
Explanation Module - Módulo de Explicación del Sistema Experto

Genera explicaciones detalladas y comprensibles sobre el razonamiento del sistema:
- Por qué se llegó a una conclusión
- Qué reglas se dispararon y en qué orden
- Qué hechos cumplieron cada regla
- Cadena completa de razonamiento

Este módulo es crucial para la transparencia y confiabilidad del sistema experto.
"""

from typing import List, Dict, Any, Optional
from app.modules.expert_system.inference.inference_engine import InferenceResult


class ExplanationModule:
    """
    Genera explicaciones del razonamiento del sistema experto.

    Ejemplo:
        explainer = ExplanationModule(inference_result)
        explanation = explainer.generate_full_explanation()
        print(explanation['summary'])
        print(explanation['reasoning_chain'])
    """

    def __init__(self, inference_result: InferenceResult):
        """
        Inicializa el módulo de explicación.

        Args:
            inference_result: Resultado de la inferencia a explicar
        """
        self.result = inference_result

    def generate_full_explanation(self) -> Dict[str, Any]:
        """
        Genera una explicación completa del razonamiento.

        Returns:
            Diccionario con la explicación completa
        """
        return {
            "summary": self.generate_summary(),
            "reasoning_chain": self.generate_reasoning_chain(),
            "conclusions_explanation": self.explain_conclusions(),
            "rules_fired_details": self.explain_rules_fired(),
            "facts_evolution": self.explain_facts_evolution(),
            "confidence_breakdown": self.explain_confidence(),
        }

    def generate_summary(self) -> str:
        """
        Genera un resumen ejecutivo del razonamiento.

        Returns:
            String con el resumen
        """
        if not self.result.success:
            return f"❌ Inference failed: {self.result.error_message}"

        summary_parts = [
            f"✅ Inference completed successfully in {self.result.iterations} iterations.",
            f"   Rules fired: {len(self.result.rules_fired)}",
            f"   Final facts: {len(self.result.final_facts)}",
            f"   Conclusions reached: {len(self.result.conclusions)}",
            f"   Execution time: {self.result.execution_time:.3f}s",
        ]

        return "\n".join(summary_parts)

    def generate_reasoning_chain(self) -> List[Dict[str, Any]]:
        """
        Genera la cadena de razonamiento paso a paso.

        Returns:
            Lista de pasos de razonamiento
        """
        chain = []

        for fired in self.result.rules_fired:
            step = {
                "step": fired["iteration"],
                "rule_name": fired["rule_name"],
                "rule_priority": fired["rule_priority"],
                "explanation": self._explain_rule_firing(fired),
                "facts_matched": fired["facts_matched"],
                "facts_added": fired["facts_added"],
            }
            chain.append(step)

        return chain

    def _explain_rule_firing(self, fired: Dict[str, Any]) -> str:
        """
        Explica por qué se disparó una regla específica.

        Args:
            fired: Información de regla disparada

        Returns:
            Texto explicativo
        """
        rule_name = fired["rule_name"]
        matched_count = len(fired["facts_matched"])
        added_count = len(fired["facts_added"])

        # Explicar las condiciones que se cumplieron
        conditions_text = []
        for fact in fired["facts_matched"]:
            conditions_text.append(
                f"  - {fact['entity']}.{fact['attribute']} = {fact['value']} (confidence: {fact['confidence']})"
            )

        # Explicar las acciones ejecutadas
        actions_text = []
        for fact in fired["facts_added"]:
            actions_text.append(
                f"  - Added: {fact['entity']}.{fact['attribute']} = {fact['value']}"
            )

        explanation = [
            f"Rule '{rule_name}' was fired because the following conditions were met:",
            *conditions_text,
            "",
            f"This rule executed the following actions:",
            *actions_text,
        ]

        return "\n".join(explanation)

    def explain_conclusions(self) -> List[Dict[str, Any]]:
        """
        Explica las conclusiones alcanzadas.

        Returns:
            Lista de explicaciones de conclusiones
        """
        explanations = []

        for conclusion in self.result.conclusions:
            conclusion_type = conclusion.get("type")

            if conclusion_type == "recommendation":
                game_id = conclusion.get("game_id")
                confidence = conclusion.get("confidence")

                # Buscar las reglas que contribuyeron a esta recomendación
                contributing_rules = self._find_contributing_rules(f"game_{game_id}")

                explanation = {
                    "type": "recommendation",
                    "game_id": game_id,
                    "confidence": confidence,
                    "reason": f"Game {game_id} was recommended with {confidence*100:.0f}% confidence.",
                    "contributing_rules": [r["rule_name"] for r in contributing_rules],
                    "details": self._explain_recommendation(game_id, contributing_rules),
                }
                explanations.append(explanation)

            elif conclusion_type == "conclusion":
                attribute = conclusion.get("attribute")
                value = conclusion.get("value")
                confidence = conclusion.get("confidence")

                explanation = {
                    "type": "conclusion",
                    "attribute": attribute,
                    "value": value,
                    "confidence": confidence,
                    "reason": f"Conclusion '{attribute}' was determined to be '{value}' with {confidence*100:.0f}% confidence.",
                }
                explanations.append(explanation)

        return explanations

    def _find_contributing_rules(self, fact_attribute: str) -> List[Dict[str, Any]]:
        """
        Encuentra las reglas que contribuyeron a un hecho específico.

        Args:
            fact_attribute: Atributo del hecho a buscar

        Returns:
            Lista de reglas que lo generaron
        """
        contributing_rules = []

        for fired in self.result.rules_fired:
            for fact_added in fired["facts_added"]:
                if fact_added.get("attribute") == fact_attribute:
                    contributing_rules.append(fired)
                    break

        return contributing_rules

    def _explain_recommendation(self, game_id: int, contributing_rules: List[Dict[str, Any]]) -> str:
        """
        Genera explicación detallada de una recomendación.

        Args:
            game_id: ID del juego recomendado
            contributing_rules: Reglas que contribuyeron

        Returns:
            Texto explicativo
        """
        if not contributing_rules:
            return f"Game {game_id} was recommended, but no specific rules were tracked."

        explanations = [f"Game {game_id} was recommended based on the following reasoning:"]

        for i, rule in enumerate(contributing_rules, 1):
            explanations.append(
                f"{i}. Rule '{rule['rule_name']}' fired in iteration {rule['iteration']} "
                f"(priority {rule['rule_priority']})"
            )

            # Mostrar condiciones que se cumplieron
            if rule['facts_matched']:
                explanations.append("   Conditions met:")
                for fact in rule['facts_matched'][:3]:  # Limitar a 3 hechos
                    explanations.append(
                        f"   - {fact['entity']}.{fact['attribute']} = {fact['value']}"
                    )

        return "\n".join(explanations)

    def explain_rules_fired(self) -> List[Dict[str, Any]]:
        """
        Proporciona detalles de todas las reglas disparadas.

        Returns:
            Lista de detalles de reglas
        """
        details = []

        for fired in self.result.rules_fired:
            detail = {
                "iteration": fired["iteration"],
                "rule_id": fired["rule_id"],
                "rule_name": fired["rule_name"],
                "priority": fired["rule_priority"],
                "conditions_met": len(fired["facts_matched"]),
                "actions_executed": len(fired["facts_added"]),
                "summary": (
                    f"Iteration {fired['iteration']}: Rule '{fired['rule_name']}' "
                    f"matched {len(fired['facts_matched'])} facts and "
                    f"added {len(fired['facts_added'])} new facts"
                ),
            }
            details.append(detail)

        return details

    def explain_facts_evolution(self) -> Dict[str, Any]:
        """
        Explica cómo evolucionó la base de hechos durante la inferencia.

        Returns:
            Diccionario con la evolución
        """
        # Contar hechos por fuente
        facts_by_source = {}
        for fact in self.result.final_facts:
            source = fact.source
            if source not in facts_by_source:
                facts_by_source[source] = 0
            facts_by_source[source] += 1

        # Contar hechos por entidad
        facts_by_entity = {}
        for fact in self.result.final_facts:
            entity = fact.entity
            if entity not in facts_by_entity:
                facts_by_entity[entity] = 0
            facts_by_entity[entity] += 1

        return {
            "total_facts": len(self.result.final_facts),
            "facts_by_source": facts_by_source,
            "facts_by_entity": facts_by_entity,
            "evolution_summary": (
                f"Started with input facts, evolved through {len(self.result.rules_fired)} "
                f"rule applications to reach {len(self.result.final_facts)} total facts."
            ),
        }

    def explain_confidence(self) -> Dict[str, Any]:
        """
        Explica los niveles de confianza de las conclusiones.

        Returns:
            Diccionario con análisis de confianza
        """
        confidence_breakdown = {
            "high_confidence": [],  # >= 0.8
            "medium_confidence": [],  # 0.5 - 0.8
            "low_confidence": [],  # < 0.5
        }

        for conclusion in self.result.conclusions:
            confidence = conclusion.get("confidence", 0.0)

            if confidence >= 0.8:
                confidence_breakdown["high_confidence"].append(conclusion)
            elif confidence >= 0.5:
                confidence_breakdown["medium_confidence"].append(conclusion)
            else:
                confidence_breakdown["low_confidence"].append(conclusion)

        return {
            "breakdown": confidence_breakdown,
            "summary": (
                f"High confidence: {len(confidence_breakdown['high_confidence'])}, "
                f"Medium confidence: {len(confidence_breakdown['medium_confidence'])}, "
                f"Low confidence: {len(confidence_breakdown['low_confidence'])}"
            ),
        }

    def generate_human_readable_explanation(self) -> str:
        """
        Genera una explicación completa en formato legible para humanos.

        Returns:
            String con explicación formateada
        """
        lines = []

        lines.append("=" * 70)
        lines.append("EXPLICACIÓN DEL RAZONAMIENTO DEL SISTEMA EXPERTO")
        lines.append("=" * 70)
        lines.append("")

        # Resumen
        lines.append(self.generate_summary())
        lines.append("")

        # Conclusiones
        lines.append("CONCLUSIONES:")
        lines.append("-" * 70)
        conclusions = self.explain_conclusions()
        for i, conclusion in enumerate(conclusions, 1):
            lines.append(f"{i}. {conclusion['reason']}")
            if conclusion.get('contributing_rules'):
                lines.append(f"   Reglas aplicadas: {', '.join(conclusion['contributing_rules'])}")
        lines.append("")

        # Cadena de razonamiento
        lines.append("CADENA DE RAZONAMIENTO:")
        lines.append("-" * 70)
        chain = self.generate_reasoning_chain()
        for step in chain:
            lines.append(f"Paso {step['step']}: {step['rule_name']}")
            lines.append(f"  Prioridad: {step['rule_priority']}")
            lines.append(f"  Hechos cumplidos: {len(step['facts_matched'])}")
            lines.append(f"  Nuevos hechos: {len(step['facts_added'])}")
        lines.append("")

        # Confianza
        lines.append("ANÁLISIS DE CONFIANZA:")
        lines.append("-" * 70)
        confidence = self.explain_confidence()
        lines.append(confidence['summary'])
        lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)

    def export_to_json(self) -> Dict[str, Any]:
        """
        Exporta la explicación completa a formato JSON.

        Returns:
            Diccionario con toda la explicación
        """
        return self.generate_full_explanation()

    def __repr__(self):
        return f"<ExplanationModule(iterations={self.result.iterations}, conclusions={len(self.result.conclusions)})>"
