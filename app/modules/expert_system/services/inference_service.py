"""
Inference Service - Servicio de Orquestación del Motor de Inferencia

Este servicio orquesta todo el proceso de inferencia:
1. Crea sesión de inferencia
2. Carga reglas y hechos desde BD
3. Ejecuta el motor de inferencia
4. Almacena resultados y logs
5. Genera explicaciones

Es el puente entre la API y el motor de inferencia.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.modules.expert_system.models.fact import Fact
from app.modules.expert_system.models.rule import Rule
from app.modules.expert_system.models.inference_session import InferenceSession
from app.modules.expert_system.models.inference_log import InferenceLog
from app.modules.expert_system.models.recommendation import Recommendation

from app.modules.expert_system.services.rule_service import RuleService
from app.modules.expert_system.services.fact_service import FactService

from app.modules.expert_system.inference.inference_engine import InferenceEngine, InferenceResult
from app.modules.expert_system.inference.explanation_module import ExplanationModule
from app.modules.expert_system.inference.conflict_resolver import ConflictResolutionStrategy


class InferenceService:
    """
    Servicio orquestador del motor de inferencia.

    Maneja todo el ciclo de vida de una sesión de inferencia:
    - Creación de sesión
    - Ejecución de inferencia
    - Almacenamiento de resultados
    - Generación de explicaciones
    """

    @staticmethod
    def run_inference(
        db: Session,
        initial_facts_data: List[Dict[str, Any]],
        goal: str = "recommend_game",
        max_iterations: int = 100,
        user_id: Optional[int] = None,
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.COMBINED,
        active_rules_only: bool = True,
    ) -> Dict[str, Any]:
        """
        Ejecuta una sesión completa de inferencia.

        Args:
            db: Sesión de base de datos
            initial_facts_data: Hechos iniciales (formato diccionario)
            goal: Objetivo de la inferencia
            max_iterations: Máximo de iteraciones
            user_id: ID del usuario (opcional)
            conflict_strategy: Estrategia de resolución de conflictos
            active_rules_only: Si solo usar reglas activas

        Returns:
            Diccionario con resultados completos de la inferencia
        """
        try:
            # PASO 1: Crear sesión de inferencia
            session = InferenceService._create_session(
                db=db,
                initial_facts_data=initial_facts_data,
                goal=goal,
                max_iterations=max_iterations,
                user_id=user_id,
            )

            # PASO 2: Cargar reglas desde BD
            rules = RuleService.get_all_rules(db, active_only=active_rules_only)

            if not rules:
                raise ValueError("No rules found in knowledge base")

            # PASO 3: Crear hechos iniciales como objetos Fact (temporales)
            initial_facts = []
            for fact_data in initial_facts_data:
                fact = Fact(
                    entity=fact_data.get("entity"),
                    attribute=fact_data.get("attribute"),
                    value=str(fact_data.get("value")),
                    value_type=fact_data.get("value_type", "string"),
                    confidence=fact_data.get("confidence", 1.0),
                    source="user_input",
                    is_temporary=True,
                    session_id=session.id,
                )
                initial_facts.append(fact)

            # Guardar hechos iniciales en BD
            db.bulk_save_objects(initial_facts)
            db.commit()

            # Recargar hechos para obtener IDs
            initial_facts = FactService.get_facts_by_session(db, session.id)

            # PASO 4: Ejecutar motor de inferencia
            print(f"🎯 Starting inference for session {session.id}")
            print(f"   Goal: {goal}")
            print(f"   Rules: {len(rules)}")
            print(f"   Initial facts: {len(initial_facts)}")

            engine = InferenceEngine(
                rules=rules,
                initial_facts=initial_facts,
                conflict_strategy=conflict_strategy,
            )

            result: InferenceResult = engine.forward_chaining(
                max_iterations=max_iterations,
                goal=goal,
            )

            # PASO 5: Actualizar sesión con resultados
            if result.success:
                session.mark_completed(
                    conclusion=result.conclusions,
                    confidence=int(InferenceService._calculate_average_confidence(result) * 100),
                )
            else:
                session.mark_failed(result.error_message or "Unknown error")

            session.iterations_performed = result.iterations
            db.commit()

            # PASO 6: Almacenar logs de inferencia
            InferenceService._store_inference_logs(db, session.id, result.rules_fired)

            # PASO 7: Crear recomendaciones si las hay
            recommendations = InferenceService._create_recommendations(db, session.id, result.conclusions)

            # PASO 8: Generar explicación
            explainer = ExplanationModule(result)
            explanation = explainer.generate_full_explanation()

            # PASO 9: Retornar resultado completo
            return {
                "session_id": session.id,
                "success": result.success,
                "status": session.status,
                "goal": goal,
                "iterations": result.iterations,
                "execution_time": result.execution_time,
                "conclusions": result.conclusions,
                "recommendations": [r.to_dict() for r in recommendations],
                "rules_fired_count": len(result.rules_fired),
                "explanation": explanation,
                "error": result.error_message,
            }

        except Exception as e:
            print(f"❌ Error during inference: {e}")
            import traceback
            traceback.print_exc()

            # Marcar sesión como fallida si existe
            if 'session' in locals():
                session.mark_failed(str(e))
                db.commit()

            raise

    @staticmethod
    def _create_session(
        db: Session,
        initial_facts_data: List[Dict[str, Any]],
        goal: str,
        max_iterations: int,
        user_id: Optional[int],
    ) -> InferenceSession:
        """Crea una nueva sesión de inferencia."""
        session = InferenceSession(
            user_id=user_id,
            status="running",
            initial_facts_json=initial_facts_data,
            goal=goal,
            max_iterations=max_iterations,
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def _store_inference_logs(db: Session, session_id: int, rules_fired: List[Dict[str, Any]]):
        """Almacena los logs de reglas disparadas."""
        logs = []

        for fired in rules_fired:
            log = InferenceLog(
                session_id=session_id,
                rule_id=fired["rule_id"],
                iteration=fired["iteration"],
                facts_matched_json=fired["facts_matched"],
                facts_added_json=fired["facts_added"],
                rule_name=fired["rule_name"],
                rule_priority=fired["rule_priority"],
            )
            logs.append(log)

        db.bulk_save_objects(logs)
        db.commit()

    @staticmethod
    def _create_recommendations(
        db: Session,
        session_id: int,
        conclusions: List[Dict[str, Any]],
    ) -> List[Recommendation]:
        """Crea registros de recomendaciones."""
        recommendations = []
        rank = 1

        for conclusion in conclusions:
            if conclusion.get("type") == "recommendation":
                game_id = conclusion.get("game_id")
                confidence = conclusion.get("confidence", 0.0)

                # TODO: Buscar título del juego en catálogo
                game_title = f"Game {game_id}"

                recommendation = Recommendation(
                    session_id=session_id,
                    game_id=game_id,
                    game_title=game_title,
                    confidence=confidence,
                    rank=rank,
                )

                recommendations.append(recommendation)
                rank += 1

        db.bulk_save_objects(recommendations)
        db.commit()

        # Recargar para obtener IDs
        return db.query(Recommendation).filter(Recommendation.session_id == session_id).all()

    @staticmethod
    def _calculate_average_confidence(result: InferenceResult) -> float:
        """Calcula la confianza promedio de las conclusiones."""
        if not result.conclusions:
            return 0.0

        total_confidence = sum(c.get("confidence", 0.0) for c in result.conclusions)
        return total_confidence / len(result.conclusions)

    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[InferenceSession]:
        """
        Obtiene una sesión de inferencia por ID.

        Args:
            db: Sesión de base de datos
            session_id: ID de la sesión

        Returns:
            Sesión si existe, None si no
        """
        return db.query(InferenceSession).filter(InferenceSession.id == session_id).first()

    @staticmethod
    def get_session_explanation(db: Session, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la explicación completa de una sesión de inferencia.

        Args:
            db: Sesión de base de datos
            session_id: ID de la sesión

        Returns:
            Explicación si existe la sesión, None si no
        """
        session = InferenceService.get_session(db, session_id)

        if not session:
            return None

        # Cargar logs
        logs = db.query(InferenceLog).filter(InferenceLog.session_id == session_id).all()

        # Cargar recomendaciones
        recommendations = db.query(Recommendation).filter(Recommendation.session_id == session_id).all()

        # Reconstruir resultado
        result = InferenceResult()
        result.success = session.status == "completed"
        result.iterations = session.iterations_performed
        result.rules_fired = [log.to_dict() for log in logs]
        result.conclusions = session.conclusion_json or []
        result.error_message = session.error_message

        # Generar explicación
        explainer = ExplanationModule(result)
        explanation = explainer.generate_full_explanation()

        return {
            "session_id": session.id,
            "status": session.status,
            "goal": session.goal,
            "iterations": session.iterations_performed,
            "confidence": session.confidence,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "conclusions": session.conclusion_json,
            "recommendations": [r.to_dict() for r in recommendations],
            "explanation": explanation,
        }

    @staticmethod
    def get_user_sessions(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
    ) -> List[InferenceSession]:
        """
        Obtiene las sesiones de inferencia de un usuario.

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            skip: Número de registros a saltar
            limit: Número máximo de registros

        Returns:
            Lista de sesiones
        """
        return (
            db.query(InferenceSession)
            .filter(InferenceSession.user_id == user_id)
            .order_by(InferenceSession.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete_session(db: Session, session_id: int) -> bool:
        """
        Elimina una sesión de inferencia y todos sus datos relacionados.

        Args:
            db: Sesión de base de datos
            session_id: ID de la sesión

        Returns:
            True si se eliminó, False si no existía
        """
        session = InferenceService.get_session(db, session_id)

        if not session:
            return False

        db.delete(session)
        db.commit()

        return True
