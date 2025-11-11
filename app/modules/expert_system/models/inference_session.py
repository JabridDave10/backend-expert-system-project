"""InferenceSession Model - Memoria de Trabajo del Sistema Experto"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class InferenceSession(Base):
    """
    Representa una sesión de inferencia (Working Memory).

    Cada sesión contiene:
    - Hechos iniciales (del usuario)
    - Hechos inferidos (generados por reglas)
    - Reglas disparadas (cadena de razonamiento)
    - Conclusión final

    Atributos:
        id: Identificador único de la sesión
        user_id: ID del usuario que inició la sesión (opcional)
        status: Estado de la sesión ("running", "completed", "failed")
        initial_facts_json: Hechos iniciales proporcionados por el usuario
        goal: Objetivo de la inferencia (ej: "recommend_game", "diagnose_preferences")
        max_iterations: Número máximo de iteraciones permitidas
        iterations_performed: Número de iteraciones realizadas
        conclusion_json: Conclusión final de la inferencia
        confidence: Nivel de confianza de la conclusión (0.0-1.0)
        error_message: Mensaje de error si la sesión falló
        created_at: Timestamp de inicio de la sesión
        completed_at: Timestamp de finalización de la sesión
    """

    __tablename__ = "inference_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id_user", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="running")  # running, completed, failed
    initial_facts_json = Column(JSON, nullable=False)
    goal = Column(String(255), default="recommend_game")
    max_iterations = Column(Integer, default=100)
    iterations_performed = Column(Integer, default=0)
    conclusion_json = Column(JSON, nullable=True)
    confidence = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    # Nota: La relación con User es opcional y se puede agregar después si se necesita
    # user = relationship("User", foreign_keys="InferenceSession.user_id")
    facts = relationship("Fact", back_populates="session", cascade="all, delete-orphan")
    inference_logs = relationship("InferenceLog", back_populates="session", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InferenceSession(id={self.id}, status={self.status}, goal={self.goal})>"

    def to_dict(self):
        """Convierte la sesión a diccionario"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "initial_facts": self.initial_facts_json,
            "goal": self.goal,
            "max_iterations": self.max_iterations,
            "iterations_performed": self.iterations_performed,
            "conclusion": self.conclusion_json,
            "confidence": self.confidence,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def mark_completed(self, conclusion, confidence):
        """Marca la sesión como completada"""
        from datetime import datetime
        self.status = "completed"
        self.conclusion_json = conclusion
        self.confidence = confidence
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error_message):
        """Marca la sesión como fallida"""
        from datetime import datetime
        self.status = "failed"
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
