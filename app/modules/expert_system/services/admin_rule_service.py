"""
Servicio de administración de reglas
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List, Tuple

from app.modules.expert_system.models.rule import Rule
from app.modules.expert_system.schemas.admin_rule_dto import (
    RuleCreateRequest,
    RuleUpdateRequest
)
from app.modules.expert_system.services.rule_service import RuleService


class AdminRuleService:
    """Servicio para operaciones CRUD avanzadas de reglas"""

    @staticmethod
    def create_rule(db: Session, rule_data: RuleCreateRequest) -> Rule:
        """
        Crear una nueva regla en la base de datos

        Args:
            db: Sesión de base de datos
            rule_data: Datos de la regla a crear

        Returns:
            Rule: Regla creada

        Raises:
            ValueError: Si ya existe una regla con ese nombre
        """
        return RuleService.create_rule(
            db=db,
            name=rule_data.name,
            description=rule_data.description,
            conditions_json=rule_data.conditions_json,
            actions_json=rule_data.actions_json,
            priority=rule_data.priority,
            category=rule_data.category,
            is_active=rule_data.active
        )

    @staticmethod
    def get_rule_by_id(db: Session, rule_id: int) -> Optional[Rule]:
        """
        Obtener una regla por su ID

        Args:
            db: Sesión de base de datos
            rule_id: ID de la regla

        Returns:
            Rule o None si no existe
        """
        return RuleService.get_rule_by_id(db, rule_id)

    @staticmethod
    def get_rules_paginated(
        db: Session,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        category: Optional[str] = None,
        active_only: bool = False,
        sort_by: str = "priority",
        sort_order: str = "desc"
    ) -> Tuple[List[Rule], int]:
        """
        Obtener reglas con paginación y filtros opcionales

        Args:
            db: Sesión de base de datos
            page: Número de página (comienza en 1)
            page_size: Cantidad de reglas por página
            search: Búsqueda por nombre o descripción (opcional)
            category: Filtrar por categoría (opcional)
            active_only: Solo reglas activas (opcional)
            sort_by: Campo por el cual ordenar (priority, name, created_at, times_fired)
            sort_order: Orden (asc, desc)

        Returns:
            Tupla con (lista de reglas, total de reglas)
        """
        query = db.query(Rule)

        # Aplicar filtro de búsqueda
        if search:
            query = query.filter(
                or_(
                    Rule.name.ilike(f"%{search}%"),
                    Rule.description.ilike(f"%{search}%")
                )
            )

        # Aplicar filtro de categoría
        if category:
            query = query.filter(Rule.category == category)

        # Aplicar filtro de activas
        if active_only:
            query = query.filter(Rule.is_active == True)

        # Contar total
        total = query.count()

        # Aplicar ordenamiento
        if sort_by == "priority":
            order_col = Rule.priority
        elif sort_by == "name":
            order_col = Rule.name
        elif sort_by == "specificity":
            order_col = Rule.specificity
        elif sort_by == "created_at":
            order_col = Rule.created_at
        else:
            order_col = Rule.priority

        if sort_order == "asc":
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        # Aplicar paginación
        offset = (page - 1) * page_size
        rules = query.offset(offset).limit(page_size).all()

        return rules, total

    @staticmethod
    def update_rule(
        db: Session,
        rule_id: int,
        rule_data: RuleUpdateRequest
    ) -> Optional[Rule]:
        """
        Actualizar una regla existente

        Args:
            db: Sesión de base de datos
            rule_id: ID de la regla a actualizar
            rule_data: Datos a actualizar

        Returns:
            Rule actualizado o None si no existe
        """
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            return None

        # Actualizar solo los campos proporcionados
        update_data = rule_data.model_dump(exclude_unset=True)

        # Mapear 'active' a 'is_active' en el modelo
        if 'active' in update_data:
            update_data['is_active'] = update_data.pop('active')

        for field, value in update_data.items():
            setattr(rule, field, value)

        # Recalcular especificidad si cambiaron las condiciones
        if 'conditions_json' in update_data:
            rule.calculate_specificity()

        db.commit()
        db.refresh(rule)

        return rule

    @staticmethod
    def delete_rule(db: Session, rule_id: int) -> bool:
        """
        Eliminar una regla

        Args:
            db: Sesión de base de datos
            rule_id: ID de la regla a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            return False

        db.delete(rule)
        db.commit()

        return True

    @staticmethod
    def bulk_delete_rules(db: Session, rule_ids: List[int]) -> Tuple[int, int]:
        """
        Eliminar múltiples reglas

        Args:
            db: Sesión de base de datos
            rule_ids: Lista de IDs de reglas a eliminar

        Returns:
            Tupla con (cantidad eliminadas, cantidad fallidas)
        """
        deleted_count = 0
        failed_count = 0

        for rule_id in rule_ids:
            if AdminRuleService.delete_rule(db, rule_id):
                deleted_count += 1
            else:
                failed_count += 1

        return deleted_count, failed_count

    @staticmethod
    def get_rule_categories(db: Session) -> List[str]:
        """
        Obtener lista de categorías de reglas

        Args:
            db: Sesión de base de datos

        Returns:
            Lista de categorías únicas
        """
        categories = db.query(Rule.category).distinct().all()
        return [c[0] for c in categories if c[0]]

    @staticmethod
    def get_rule_stats(db: Session) -> dict:
        """
        Obtener estadísticas de las reglas

        Args:
            db: Sesión de base de datos

        Returns:
            Dict con estadísticas
        """
        total_rules = db.query(func.count(Rule.id)).scalar()
        active_rules = db.query(func.count(Rule.id)).filter(Rule.is_active == True).scalar()
        inactive_rules = total_rules - active_rules

        # Reglas por categoría
        categories_stats = db.query(
            Rule.category,
            func.count(Rule.id).label('count')
        ).group_by(Rule.category).order_by(func.count(Rule.id).desc()).all()

        # Contar usos desde inference_logs
        from app.modules.expert_system.models.inference_log import InferenceLog
        total_fires = db.query(func.count(InferenceLog.id)).scalar() or 0

        # Reglas más usadas (top 10) basadas en inference_logs
        most_fired_stats = db.query(
            Rule.id,
            Rule.name,
            Rule.category,
            func.count(InferenceLog.id).label('usage_count')
        ).outerjoin(InferenceLog, Rule.id == InferenceLog.rule_id)\
         .group_by(Rule.id, Rule.name, Rule.category)\
         .order_by(func.count(InferenceLog.id).desc())\
         .limit(10).all()

        return {
            "total_rules": total_rules,
            "active_rules": active_rules,
            "inactive_rules": inactive_rules,
            "total_fires": total_fires,
            "categories": [{"category": c[0], "count": c[1]} for c in categories_stats if c[0]],
            "most_fired": [
                {
                    "id": r[0],
                    "name": r[1],
                    "category": r[2],
                    "times_fired": r[3]
                }
                for r in most_fired_stats
            ]
        }

    @staticmethod
    def toggle_rule_active(db: Session, rule_id: int) -> Optional[Rule]:
        """
        Alternar el estado activo/inactivo de una regla

        Args:
            db: Sesión de base de datos
            rule_id: ID de la regla

        Returns:
            Rule actualizada o None si no existe
        """
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            return None

        rule.is_active = not rule.is_active
        db.commit()
        db.refresh(rule)

        return rule

    @staticmethod
    def duplicate_rule(db: Session, rule_id: int, new_name: str) -> Optional[Rule]:
        """
        Duplicar una regla existente con un nuevo nombre

        Args:
            db: Sesión de base de datos
            rule_id: ID de la regla a duplicar
            new_name: Nombre para la nueva regla

        Returns:
            Rule duplicada o None si la original no existe

        Raises:
            ValueError: Si ya existe una regla con el nuevo nombre
        """
        original_rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not original_rule:
            return None

        # Verificar que el nuevo nombre no exista
        existing = db.query(Rule).filter(Rule.name == new_name).first()
        if existing:
            raise ValueError(f"Ya existe una regla con el nombre '{new_name}'")

        # Crear regla duplicada
        new_rule = Rule(
            name=new_name,
            description=f"{original_rule.description} (copia)",
            conditions_json=original_rule.conditions_json,
            actions_json=original_rule.actions_json,
            priority=original_rule.priority,
            category=original_rule.category,
            is_active=False  # Las copias empiezan inactivas por seguridad
        )

        new_rule.calculate_specificity()

        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)

        return new_rule
