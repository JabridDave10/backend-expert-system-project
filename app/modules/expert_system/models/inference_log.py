"""InferenceLog Model - Log de Trazabilidad del Sistema Experto"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class InferenceLog(Base):
    """
    Registra cada regla disparada durante una sesión de inferencia.

    Permite trazabilidad completa del razonamiento para explicaciones y auditoría.

    Atributos:
        id: Identificador único del log
        session_id: ID de la sesión de inferencia
        rule_id: ID de la regla que se disparó
        iteration: Número de iteración en la que se disparó
        facts_matched_json: Hechos que cumplieron las condiciones
        facts_added_json: Nuevos hechos agregados por la regla
        rule_name: Nombre de la regla (desnormalizado para performance)
        rule_priority: Prioridad de la regla (desnormalizado)
        timestamp: Timestamp de cuándo se disparó la regla
    """

    __tablename__ = "inference_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("inference_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False)
    iteration = Column(Integer, nullable=False)
    facts_matched_json = Column(JSON, nullable=False)  # Hechos que cumplieron condiciones
    facts_added_json = Column(JSON, nullable=False)  # Nuevos hechos agregados
    rule_name = Column(String(255), nullable=False)  # Desnormalizado para performance
    rule_priority = Column(Integer, default=0)  # Desnormalizado
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("InferenceSession", back_populates="inference_logs")
    rule = relationship("Rule", back_populates="inference_logs")

    def __repr__(self):
        return f"<InferenceLog(session={self.session_id}, rule={self.rule_name}, iter={self.iteration})>"

    def to_dict(self):
        """Convierte el log a diccionario"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "rule_priority": self.rule_priority,
            "iteration": self.iteration,
            "facts_matched": self.facts_matched_json,
            "facts_added": self.facts_added_json,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def get_summary(self):
        """Retorna un resumen legible del log"""
        matched_count = len(self.facts_matched_json) if self.facts_matched_json else 0
        added_count = len(self.facts_added_json) if self.facts_added_json else 0
        return f"Iter {self.iteration}: Rule '{self.rule_name}' fired (matched {matched_count} facts, added {added_count} facts)"
