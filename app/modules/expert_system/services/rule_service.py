"""
Rule Service - Servicio de Gestión de Reglas

Proporciona operaciones CRUD y lógica de negocio para reglas del sistema experto.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.modules.expert_system.models.rule import Rule


class RuleService:
    """
    Servicio para gestionar reglas de la base de conocimiento.
    """

    @staticmethod
    def create_rule(
        db: Session,
        name: str,
        conditions_json: List[dict],
        actions_json: List[dict],
        description: Optional[str] = None,
        priority: int = 0,
        category: str = "general",
        is_active: bool = True,
    ) -> Rule:
        """
        Crea una nueva regla.

        Args:
            db: Sesión de base de datos
            name: Nombre de la regla
            conditions_json: Lista de condiciones IF
            actions_json: Lista de acciones THEN
            description: Descripción opcional
            priority: Prioridad de la regla
            category: Categoría de la regla
            is_active: Si la regla está activa

        Returns:
            Regla creada

        Raises:
            ValueError: Si el nombre ya existe
        """
        try:
            rule = Rule(
                name=name,
                description=description,
                conditions_json=conditions_json,
                actions_json=actions_json,
                priority=priority,
                category=category,
                is_active=is_active,
            )

            # Calcular especificidad automáticamente
            rule.calculate_specificity()

            db.add(rule)
            db.commit()
            db.refresh(rule)

            return rule

        except IntegrityError:
            db.rollback()
            raise ValueError(f"Rule with name '{name}' already exists")

    @staticmethod
    def get_rule_by_id(db: Session, rule_id: int) -> Optional[Rule]:
        """
        Obtiene una regla por su ID.

        Args:
            db: Sesión de base de datos
            rule_id: ID de la regla

        Returns:
            Regla si existe, None si no
        """
        return db.query(Rule).filter(Rule.id == rule_id).first()

    @staticmethod
    def get_rule_by_name(db: Session, name: str) -> Optional[Rule]:
        """
        Obtiene una regla por su nombre.

        Args:
            db: Sesión de base de datos
            name: Nombre de la regla

        Returns:
            Regla si existe, None si no
        """
        return db.query(Rule).filter(Rule.name == name).first()

    @staticmethod
    def get_all_rules(
        db: Session,
        active_only: bool = False,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Rule]:
        """
        Obtiene todas las reglas con filtros opcionales.

        Args:
            db: Sesión de base de datos
            active_only: Si solo retornar reglas activas
            category: Filtrar por categoría
            skip: Número de registros a saltar (paginación)
            limit: Número máximo de registros a retornar

        Returns:
            Lista de reglas
        """
        query = db.query(Rule)

        if active_only:
            query = query.filter(Rule.is_active == True)

        if category:
            query = query.filter(Rule.category == category)

        # Ordenar por prioridad descendente
        query = query.order_by(Rule.priority.desc(), Rule.id.desc())

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_rule(
        db: Session,
        rule_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        conditions_json: Optional[List[dict]] = None,
        actions_json: Optional[List[dict]] = None,
        priority: Optional[int] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Rule]:
        """
        Actualiza una regla existente.

        Args:
            db: Sesión de base de datos
            rule_id: ID de la regla a actualizar
            name: Nuevo nombre (opcional)
            description: Nueva descripción (opcional)
            conditions_json: Nuevas condiciones (opcional)
            actions_json: Nuevas acciones (opcional)
            priority: Nueva prioridad (opcional)
            category: Nueva categoría (opcional)
            is_active: Nuevo estado (opcional)

        Returns:
            Regla actualizada si existe, None si no

        Raises:
            ValueError: Si el nuevo nombre ya existe
        """
        rule = RuleService.get_rule_by_id(db, rule_id)

        if not rule:
            return None

        try:
            if name is not None:
                rule.name = name
            if description is not None:
                rule.description = description
            if conditions_json is not None:
                rule.conditions_json = conditions_json
                rule.calculate_specificity()  # Recalcular especificidad
            if actions_json is not None:
                rule.actions_json = actions_json
            if priority is not None:
                rule.priority = priority
            if category is not None:
                rule.category = category
            if is_active is not None:
                rule.is_active = is_active

            db.commit()
            db.refresh(rule)

            return rule

        except IntegrityError:
            db.rollback()
            raise ValueError(f"Rule with name '{name}' already exists")

    @staticmethod
    def delete_rule(db: Session, rule_id: int) -> bool:
        """
        Elimina una regla.

        Args:
            db: Sesión de base de datos
            rule_id: ID de la regla a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        rule = RuleService.get_rule_by_id(db, rule_id)

        if not rule:
            return False

        db.delete(rule)
        db.commit()

        return True

    @staticmethod
    def activate_rule(db: Session, rule_id: int) -> Optional[Rule]:
        """
        Activa una regla desactivada.

        Args:
            db: Sesión de base de datos
            rule_id: ID de la regla

        Returns:
            Regla activada si existe, None si no
        """
        return RuleService.update_rule(db, rule_id, is_active=True)

    @staticmethod
    def deactivate_rule(db: Session, rule_id: int) -> Optional[Rule]:
        """
        Desactiva una regla activa.

        Args:
            db: Sesión de base de datos
            rule_id: ID de la regla

        Returns:
            Regla desactivada si existe, None si no
        """
        return RuleService.update_rule(db, rule_id, is_active=False)

    @staticmethod
    def count_rules(db: Session, active_only: bool = False) -> int:
        """
        Cuenta el número total de reglas.

        Args:
            db: Sesión de base de datos
            active_only: Si solo contar reglas activas

        Returns:
            Número de reglas
        """
        query = db.query(Rule)

        if active_only:
            query = query.filter(Rule.is_active == True)

        return query.count()

    @staticmethod
    def get_rules_by_category(db: Session, category: str) -> List[Rule]:
        """
        Obtiene todas las reglas de una categoría específica.

        Args:
            db: Sesión de base de datos
            category: Categoría a buscar

        Returns:
            Lista de reglas
        """
        return RuleService.get_all_rules(db, category=category)
