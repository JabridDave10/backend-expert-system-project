"""Rule Model - Base de Reglas del Sistema Experto"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Rule(Base):
    """
    Representa una regla de producción IF-THEN en la base de conocimiento.

    Formato: IF (condiciones) THEN (acciones)

    Ejemplo de regla:
    {
        "name": "Recomendar RPG para adultos",
        "conditions": [
            {"entity": "user", "attribute": "age", "operator": ">=", "value": 18},
            {"entity": "user", "attribute": "prefers_genre", "operator": "==", "value": "RPG"}
        ],
        "actions": [
            {"action": "add_fact", "entity": "recommendation", "attribute": "game_id", "value": 4},
            {"action": "add_fact", "entity": "recommendation", "attribute": "confidence", "value": 0.9}
        ],
        "priority": 10
    }

    Atributos:
        id: Identificador único de la regla
        name: Nombre descriptivo de la regla
        description: Descripción detallada de qué hace la regla
        conditions_json: Condiciones IF en formato JSON (lista de diccionarios)
        actions_json: Acciones THEN en formato JSON (lista de diccionarios)
        priority: Prioridad/salience para resolución de conflictos (mayor = más prioritario)
        specificity: Número de condiciones (calculado automáticamente)
        is_active: Si la regla está activa o desactivada
        category: Categoría de la regla (ej: "recommendation", "filtering", "scoring")
        created_at: Timestamp de creación
        updated_at: Timestamp de última modificación
    """

    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    conditions_json = Column(JSON, nullable=False)  # Lista de condiciones IF
    actions_json = Column(JSON, nullable=False)  # Lista de acciones THEN
    priority = Column(Integer, default=0)  # Mayor prioridad = se ejecuta primero
    specificity = Column(Integer, default=0)  # Número de condiciones (auto-calculado)
    is_active = Column(Boolean, default=True)
    category = Column(String(100), default="general")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    inference_logs = relationship("InferenceLog", back_populates="rule")

    def __repr__(self):
        return f"<Rule(name={self.name}, priority={self.priority}, active={self.is_active})>"

    def to_dict(self):
        """Convierte la regla a diccionario"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions_json,
            "actions": self.actions_json,
            "priority": self.priority,
            "specificity": self.specificity,
            "is_active": self.is_active,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def calculate_specificity(self):
        """Calcula la especificidad basada en el número de condiciones"""
        if isinstance(self.conditions_json, list):
            self.specificity = len(self.conditions_json)
        else:
            self.specificity = 0
        return self.specificity

    def get_condition_summary(self):
        """Retorna un resumen legible de las condiciones"""
        if not self.conditions_json:
            return "No conditions"

        summaries = []
        for cond in self.conditions_json:
            entity = cond.get("entity", "?")
            attr = cond.get("attribute", "?")
            op = cond.get("operator", "?")
            val = cond.get("value", "?")
            summaries.append(f"{entity}.{attr} {op} {val}")

        return " AND ".join(summaries)

    def get_action_summary(self):
        """Retorna un resumen legible de las acciones"""
        if not self.actions_json:
            return "No actions"

        summaries = []
        for action in self.actions_json:
            action_type = action.get("action", "?")
            if action_type == "add_fact":
                entity = action.get("entity", "?")
                attr = action.get("attribute", "?")
                val = action.get("value", "?")
                summaries.append(f"Add {entity}.{attr} = {val}")
            elif action_type == "recommend":
                game_id = action.get("game_id", "?")
                conf = action.get("confidence", "?")
                summaries.append(f"Recommend game {game_id} (conf: {conf})")
            else:
                summaries.append(str(action))

        return ", ".join(summaries)
