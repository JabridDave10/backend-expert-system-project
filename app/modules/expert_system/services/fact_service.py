"""
Fact Service - Servicio de Gestión de Hechos

Proporciona operaciones CRUD y lógica de negocio para hechos del sistema experto.
"""

from typing import List, Optional, Any
from sqlalchemy.orm import Session
from app.modules.expert_system.models.fact import Fact


class FactService:
    """
    Servicio para gestionar hechos de la base de conocimiento.
    """

    @staticmethod
    def create_fact(
        db: Session,
        entity: str,
        attribute: str,
        value: Any,
        value_type: str = "string",
        confidence: float = 1.0,
        source: str = "user_input",
        is_temporary: bool = False,
        session_id: Optional[int] = None,
    ) -> Fact:
        """
        Crea un nuevo hecho.

        Args:
            db: Sesión de base de datos
            entity: Entidad del hecho
            attribute: Atributo del hecho
            value: Valor del hecho
            value_type: Tipo del valor
            confidence: Confianza del hecho (0.0-1.0)
            source: Fuente del hecho
            is_temporary: Si es temporal
            session_id: ID de sesión si es temporal

        Returns:
            Hecho creado
        """
        fact = Fact(
            entity=entity,
            attribute=attribute,
            value=str(value),
            value_type=value_type,
            confidence=confidence,
            source=source,
            is_temporary=is_temporary,
            session_id=session_id,
        )

        db.add(fact)
        db.commit()
        db.refresh(fact)

        return fact

    @staticmethod
    def get_fact_by_id(db: Session, fact_id: int) -> Optional[Fact]:
        """
        Obtiene un hecho por su ID.

        Args:
            db: Sesión de base de datos
            fact_id: ID del hecho

        Returns:
            Hecho si existe, None si no
        """
        return db.query(Fact).filter(Fact.id == fact_id).first()

    @staticmethod
    def get_fact(db: Session, entity: str, attribute: str) -> Optional[Fact]:
        """
        Obtiene un hecho por entidad y atributo.

        Args:
            db: Sesión de base de datos
            entity: Entidad del hecho
            attribute: Atributo del hecho

        Returns:
            Hecho más reciente si existe, None si no
        """
        return (
            db.query(Fact)
            .filter(Fact.entity == entity, Fact.attribute == attribute)
            .order_by(Fact.created_at.desc())
            .first()
        )

    @staticmethod
    def get_facts_by_entity(db: Session, entity: str) -> List[Fact]:
        """
        Obtiene todos los hechos de una entidad.

        Args:
            db: Sesión de base de datos
            entity: Entidad a buscar

        Returns:
            Lista de hechos
        """
        return db.query(Fact).filter(Fact.entity == entity).all()

    @staticmethod
    def get_facts_by_source(db: Session, source: str) -> List[Fact]:
        """
        Obtiene todos los hechos de una fuente específica.

        Args:
            db: Sesión de base de datos
            source: Fuente a buscar

        Returns:
            Lista de hechos
        """
        return db.query(Fact).filter(Fact.source == source).all()

    @staticmethod
    def get_facts_by_session(db: Session, session_id: int) -> List[Fact]:
        """
        Obtiene todos los hechos de una sesión específica.

        Args:
            db: Sesión de base de datos
            session_id: ID de la sesión

        Returns:
            Lista de hechos
        """
        return db.query(Fact).filter(Fact.session_id == session_id).all()

    @staticmethod
    def get_all_facts(
        db: Session,
        persistent_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Fact]:
        """
        Obtiene todos los hechos con filtros opcionales.

        Args:
            db: Sesión de base de datos
            persistent_only: Si solo retornar hechos persistentes
            skip: Número de registros a saltar
            limit: Número máximo de registros

        Returns:
            Lista de hechos
        """
        query = db.query(Fact)

        if persistent_only:
            query = query.filter(Fact.is_temporary == False)

        return query.order_by(Fact.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_fact(
        db: Session,
        fact_id: int,
        value: Optional[Any] = None,
        confidence: Optional[float] = None,
        value_type: Optional[str] = None,
    ) -> Optional[Fact]:
        """
        Actualiza un hecho existente.

        Args:
            db: Sesión de base de datos
            fact_id: ID del hecho
            value: Nuevo valor (opcional)
            confidence: Nueva confianza (opcional)
            value_type: Nuevo tipo (opcional)

        Returns:
            Hecho actualizado si existe, None si no
        """
        fact = FactService.get_fact_by_id(db, fact_id)

        if not fact:
            return None

        if value is not None:
            fact.value = str(value)
        if confidence is not None:
            fact.confidence = confidence
        if value_type is not None:
            fact.value_type = value_type

        db.commit()
        db.refresh(fact)

        return fact

    @staticmethod
    def delete_fact(db: Session, fact_id: int) -> bool:
        """
        Elimina un hecho.

        Args:
            db: Sesión de base de datos
            fact_id: ID del hecho

        Returns:
            True si se eliminó, False si no existía
        """
        fact = FactService.get_fact_by_id(db, fact_id)

        if not fact:
            return False

        db.delete(fact)
        db.commit()

        return True

    @staticmethod
    def delete_temporary_facts(db: Session, session_id: Optional[int] = None) -> int:
        """
        Elimina hechos temporales.

        Args:
            db: Sesión de base de datos
            session_id: ID de sesión específica (opcional)

        Returns:
            Número de hechos eliminados
        """
        query = db.query(Fact).filter(Fact.is_temporary == True)

        if session_id is not None:
            query = query.filter(Fact.session_id == session_id)

        count = query.count()
        query.delete()
        db.commit()

        return count

    @staticmethod
    def count_facts(db: Session, persistent_only: bool = False) -> int:
        """
        Cuenta el número total de hechos.

        Args:
            db: Sesión de base de datos
            persistent_only: Si solo contar hechos persistentes

        Returns:
            Número de hechos
        """
        query = db.query(Fact)

        if persistent_only:
            query = query.filter(Fact.is_temporary == False)

        return query.count()

    @staticmethod
    def upsert_fact(
        db: Session,
        entity: str,
        attribute: str,
        value: Any,
        value_type: str = "string",
        confidence: float = 1.0,
        source: str = "user_input",
    ) -> Fact:
        """
        Inserta o actualiza un hecho (upsert).

        Si ya existe un hecho con la misma entidad y atributo, lo actualiza.
        Si no existe, crea uno nuevo.

        Args:
            db: Sesión de base de datos
            entity: Entidad del hecho
            attribute: Atributo del hecho
            value: Valor del hecho
            value_type: Tipo del valor
            confidence: Confianza del hecho
            source: Fuente del hecho

        Returns:
            Hecho creado o actualizado
        """
        existing_fact = FactService.get_fact(db, entity, attribute)

        if existing_fact:
            # Actualizar hecho existente
            existing_fact.value = str(value)
            existing_fact.value_type = value_type
            existing_fact.confidence = confidence
            existing_fact.source = source

            db.commit()
            db.refresh(existing_fact)

            return existing_fact
        else:
            # Crear nuevo hecho
            return FactService.create_fact(
                db=db,
                entity=entity,
                attribute=attribute,
                value=value,
                value_type=value_type,
                confidence=confidence,
                source=source,
            )

    @staticmethod
    def create_facts_bulk(db: Session, facts_data: List[dict]) -> List[Fact]:
        """
        Crea múltiples hechos en una sola transacción.

        Args:
            db: Sesión de base de datos
            facts_data: Lista de diccionarios con datos de hechos

        Returns:
            Lista de hechos creados
        """
        facts = []

        for data in facts_data:
            fact = Fact(
                entity=data.get("entity"),
                attribute=data.get("attribute"),
                value=str(data.get("value")),
                value_type=data.get("value_type", "string"),
                confidence=data.get("confidence", 1.0),
                source=data.get("source", "user_input"),
                is_temporary=data.get("is_temporary", False),
                session_id=data.get("session_id"),
            )
            facts.append(fact)
            db.add(fact)

        db.commit()

        for fact in facts:
            db.refresh(fact)

        return facts
