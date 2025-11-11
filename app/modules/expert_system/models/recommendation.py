"""Recommendation Model - Recomendaciones Generadas por el Sistema Experto"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Recommendation(Base):
    """
    Representa una recomendación de juego generada por el sistema experto.

    Atributos:
        id: Identificador único de la recomendación
        session_id: ID de la sesión de inferencia que generó la recomendación
        game_id: ID del juego recomendado (del catálogo)
        game_title: Título del juego (desnormalizado)
        confidence: Nivel de confianza de la recomendación (0.0-1.0)
        score: Puntaje calculado por el sistema
        justification: Explicación de por qué se recomendó este juego
        rules_applied: Lista de nombres de reglas que contribuyeron
        reasons_json: Razones estructuradas (JSON) de la recomendación
        rank: Posición en el ranking (1 = mejor recomendación)
        created_at: Timestamp de creación
    """

    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("inference_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    game_id = Column(Integer, nullable=False, index=True)
    game_title = Column(String(255), nullable=False)
    confidence = Column(Float, default=0.0)  # 0.0 a 1.0
    score = Column(Float, default=0.0)
    justification = Column(Text, nullable=True)
    rules_applied = Column(JSON, nullable=True)  # Lista de nombres de reglas
    reasons_json = Column(JSON, nullable=True)  # Razones estructuradas
    rank = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("InferenceSession", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation(game={self.game_title}, confidence={self.confidence}, rank={self.rank})>"

    def to_dict(self):
        """Convierte la recomendación a diccionario"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "game_id": self.game_id,
            "game_title": self.game_title,
            "confidence": self.confidence,
            "score": self.score,
            "justification": self.justification,
            "rules_applied": self.rules_applied,
            "reasons": self.reasons_json,
            "rank": self.rank,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def add_reason(self, reason: str, weight: float = 1.0):
        """Agrega una razón a la justificación"""
        if self.reasons_json is None:
            self.reasons_json = []

        self.reasons_json.append({
            "reason": reason,
            "weight": weight,
        })

    def build_justification(self):
        """Construye el texto de justificación a partir de las razones"""
        if not self.reasons_json:
            self.justification = "No specific reasons provided."
            return

        reasons_text = []
        for i, reason_obj in enumerate(self.reasons_json, 1):
            reasons_text.append(f"{i}. {reason_obj['reason']}")

        self.justification = "\n".join(reasons_text)
