"""GameRule Model - Tabla de asociación entre juegos y reglas"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Table
from sqlalchemy.sql import func
from app.core.database import Base


class GameRule(Base):
    """
    Tabla de asociación entre juegos y reglas.

    Permite asignar reglas específicas a juegos específicos,
    creando relaciones personalizadas para el sistema experto.

    Atributos:
        id: Identificador único de la asociación
        game_id: ID del juego (referencia a games.id)
        rule_id: ID de la regla (referencia a rules.id)
        created_at: Timestamp de cuando se asignó la regla al juego
    """

    __tablename__ = "game_rules"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<GameRule(game_id={self.game_id}, rule_id={self.rule_id})>"

    def to_dict(self):
        """Convierte la asociación a diccionario"""
        return {
            "id": self.id,
            "game_id": self.game_id,
            "rule_id": self.rule_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
