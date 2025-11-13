"""Fact Model - Base de Hechos del Sistema Experto"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Fact(Base):
    """
    Representa un hecho atómico en la base de conocimiento.

    Un hecho tiene la forma: (entidad, atributo, valor, confianza)
    Ejemplo: (user_123, "prefers_genre", "RPG", 1.0)

    Atributos:
        id: Identificador único del hecho
        entity: Entidad sobre la que se afirma el hecho (ej: "user_123", "game_456")
        attribute: Atributo o propiedad de la entidad (ej: "age", "prefers_genre")
        value: Valor del atributo (almacenado como texto, se parsea según tipo)
        value_type: Tipo del valor ("string", "int", "float", "bool")
        confidence: Nivel de confianza/certeza del hecho (0.0-1.0)
        source: Origen del hecho ("user_input", "inferred", "database", "external_api")
        is_temporary: Si es temporal (se borra al finalizar sesión) o persistente
        session_id: ID de sesión de inferencia si es temporal
        created_at: Timestamp de creación
    """

    __tablename__ = "facts"

    id = Column(Integer, primary_key=True, index=True)
    entity = Column(String(255), nullable=False, index=True)
    attribute = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(50), default="string")  # string, int, float, bool, list
    confidence = Column(Float, default=1.0)  # 0.0 a 1.0
    source = Column(String(100), default="user_input")  # user_input, inferred, database, external_api
    is_temporary = Column(Boolean, default=False)
    session_id = Column(Integer, ForeignKey("inference_sessions.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("InferenceSession", back_populates="facts")

    def __repr__(self):
        return f"<Fact({self.entity}.{self.attribute} = {self.value} [conf: {self.confidence}])>"

    def to_dict(self):
        """Convierte el hecho a diccionario"""
        return {
            "id": self.id,
            "entity": self.entity,
            "attribute": self.attribute,
            "value": self.value,
            "value_type": self.value_type,
            "confidence": self.confidence,
            "source": self.source,
            "is_temporary": self.is_temporary,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_typed_value(self):
        """Retorna el valor con el tipo correcto"""
        # Normalizar aliases de tipos
        value_type = self.value_type.lower() if self.value_type else "string"

        if value_type in ("int", "integer"):
            return int(self.value)
        elif value_type == "float":
            return float(self.value)
        elif value_type in ("bool", "boolean"):
            return self.value.lower() in ("true", "1", "yes")
        elif value_type == "list":
            import json
            return json.loads(self.value)
        else:
            return self.value
