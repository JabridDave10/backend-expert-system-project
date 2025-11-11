"""
Knowledge Router - API de Gestión de Conocimiento

Proporciona endpoints REST para gestionar la base de conocimiento:
- CRUD de Reglas
- CRUD de Hechos
- Estadísticas y consultas
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import SessionLocal
from app.modules.expert_system.services.rule_service import RuleService
from app.modules.expert_system.services.fact_service import FactService
from app.modules.expert_system.schemas.rule_dto import (
    CreateRuleDTO,
    UpdateRuleDTO,
    RuleDTO,
    RuleListResponse,
    RuleSummaryDTO,
)
from app.modules.expert_system.schemas.fact_dto import (
    CreateFactDTO,
    UpdateFactDTO,
    FactDTO,
    FactListResponse,
)


router = APIRouter(prefix="/knowledge", tags=["knowledge-base"])


# Dependency para obtener DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===========================
# ENDPOINTS DE REGLAS
# ===========================

@router.post("/rules", response_model=RuleDTO, status_code=201)
async def create_rule(rule_data: CreateRuleDTO, db: Session = Depends(get_db)):
    """
    Crea una nueva regla en la base de conocimiento.

    Args:
        rule_data: Datos de la regla

    Returns:
        Regla creada
    """
    try:
        # Convertir Pydantic models a dicts
        conditions_json = [cond.model_dump() for cond in rule_data.conditions]
        actions_json = [action.model_dump() for action in rule_data.actions]

        rule = RuleService.create_rule(
            db=db,
            name=rule_data.name,
            description=rule_data.description,
            conditions_json=conditions_json,
            actions_json=actions_json,
            priority=rule_data.priority,
            category=rule_data.category,
            is_active=rule_data.is_active,
        )

        return RuleDTO.model_validate(rule)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating rule: {str(e)}")


@router.get("/rules", response_model=RuleListResponse)
async def get_all_rules(
    active_only: bool = Query(False, description="Solo reglas activas"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    db: Session = Depends(get_db),
):
    """
    Obtiene todas las reglas con filtros opcionales.

    Args:
        active_only: Si solo retornar reglas activas
        category: Filtrar por categoría
        page: Número de página
        page_size: Tamaño de página

    Returns:
        Lista de reglas
    """
    skip = (page - 1) * page_size

    rules = RuleService.get_all_rules(
        db=db,
        active_only=active_only,
        category=category,
        skip=skip,
        limit=page_size,
    )

    total = RuleService.count_rules(db=db, active_only=active_only)

    return RuleListResponse(
        rules=[RuleDTO.model_validate(r) for r in rules],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/rules/{rule_id}", response_model=RuleDTO)
async def get_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Obtiene una regla por su ID.

    Args:
        rule_id: ID de la regla

    Returns:
        Regla solicitada
    """
    rule = RuleService.get_rule_by_id(db, rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found")

    return RuleDTO.model_validate(rule)


@router.put("/rules/{rule_id}", response_model=RuleDTO)
async def update_rule(
    rule_id: int,
    rule_data: UpdateRuleDTO,
    db: Session = Depends(get_db),
):
    """
    Actualiza una regla existente.

    Args:
        rule_id: ID de la regla
        rule_data: Datos a actualizar

    Returns:
        Regla actualizada
    """
    try:
        # Convertir listas de Pydantic models a dicts si existen
        conditions_json = None
        if rule_data.conditions:
            conditions_json = [cond.model_dump() for cond in rule_data.conditions]

        actions_json = None
        if rule_data.actions:
            actions_json = [action.model_dump() for action in rule_data.actions]

        rule = RuleService.update_rule(
            db=db,
            rule_id=rule_id,
            name=rule_data.name,
            description=rule_data.description,
            conditions_json=conditions_json,
            actions_json=actions_json,
            priority=rule_data.priority,
            category=rule_data.category,
            is_active=rule_data.is_active,
        )

        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found")

        return RuleDTO.model_validate(rule)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating rule: {str(e)}")


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Elimina una regla.

    Args:
        rule_id: ID de la regla
    """
    success = RuleService.delete_rule(db, rule_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found")


@router.post("/rules/{rule_id}/activate", response_model=RuleDTO)
async def activate_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Activa una regla desactivada.

    Args:
        rule_id: ID de la regla

    Returns:
        Regla activada
    """
    rule = RuleService.activate_rule(db, rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found")

    return RuleDTO.model_validate(rule)


@router.post("/rules/{rule_id}/deactivate", response_model=RuleDTO)
async def deactivate_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Desactiva una regla activa.

    Args:
        rule_id: ID de la regla

    Returns:
        Regla desactivada
    """
    rule = RuleService.deactivate_rule(db, rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found")

    return RuleDTO.model_validate(rule)


# ===========================
# ENDPOINTS DE HECHOS
# ===========================

@router.post("/facts", response_model=FactDTO, status_code=201)
async def create_fact(fact_data: CreateFactDTO, db: Session = Depends(get_db)):
    """
    Crea un nuevo hecho en la base de conocimiento.

    Args:
        fact_data: Datos del hecho

    Returns:
        Hecho creado
    """
    try:
        fact = FactService.create_fact(
            db=db,
            entity=fact_data.entity,
            attribute=fact_data.attribute,
            value=fact_data.value,
            value_type=fact_data.value_type,
            confidence=fact_data.confidence,
            source=fact_data.source,
            is_temporary=fact_data.is_temporary,
            session_id=fact_data.session_id,
        )

        return FactDTO.model_validate(fact)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating fact: {str(e)}")


@router.get("/facts", response_model=FactListResponse)
async def get_all_facts(
    persistent_only: bool = Query(False, description="Solo hechos persistentes"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    db: Session = Depends(get_db),
):
    """
    Obtiene todos los hechos con filtros opcionales.

    Args:
        persistent_only: Si solo retornar hechos persistentes
        page: Número de página
        page_size: Tamaño de página

    Returns:
        Lista de hechos
    """
    skip = (page - 1) * page_size

    facts = FactService.get_all_facts(
        db=db,
        persistent_only=persistent_only,
        skip=skip,
        limit=page_size,
    )

    total = FactService.count_facts(db=db, persistent_only=persistent_only)

    return FactListResponse(
        facts=[FactDTO.model_validate(f) for f in facts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/facts/{fact_id}", response_model=FactDTO)
async def get_fact(fact_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un hecho por su ID.

    Args:
        fact_id: ID del hecho

    Returns:
        Hecho solicitado
    """
    fact = FactService.get_fact_by_id(db, fact_id)

    if not fact:
        raise HTTPException(status_code=404, detail=f"Fact with ID {fact_id} not found")

    return FactDTO.model_validate(fact)


@router.get("/facts/entity/{entity}", response_model=List[FactDTO])
async def get_facts_by_entity(entity: str, db: Session = Depends(get_db)):
    """
    Obtiene todos los hechos de una entidad específica.

    Args:
        entity: Entidad a buscar

    Returns:
        Lista de hechos
    """
    facts = FactService.get_facts_by_entity(db, entity)

    return [FactDTO.model_validate(f) for f in facts]


@router.put("/facts/{fact_id}", response_model=FactDTO)
async def update_fact(
    fact_id: int,
    fact_data: UpdateFactDTO,
    db: Session = Depends(get_db),
):
    """
    Actualiza un hecho existente.

    Args:
        fact_id: ID del hecho
        fact_data: Datos a actualizar

    Returns:
        Hecho actualizado
    """
    try:
        fact = FactService.update_fact(
            db=db,
            fact_id=fact_id,
            value=fact_data.value,
            confidence=fact_data.confidence,
            value_type=fact_data.value_type,
        )

        if not fact:
            raise HTTPException(status_code=404, detail=f"Fact with ID {fact_id} not found")

        return FactDTO.model_validate(fact)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating fact: {str(e)}")


@router.delete("/facts/{fact_id}", status_code=204)
async def delete_fact(fact_id: int, db: Session = Depends(get_db)):
    """
    Elimina un hecho.

    Args:
        fact_id: ID del hecho
    """
    success = FactService.delete_fact(db, fact_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Fact with ID {fact_id} not found")


# ===========================
# ENDPOINTS DE ESTADÍSTICAS
# ===========================

@router.get("/stats")
async def get_knowledge_stats(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de la base de conocimiento.

    Returns:
        Estadísticas generales
    """
    return {
        "rules": {
            "total": RuleService.count_rules(db, active_only=False),
            "active": RuleService.count_rules(db, active_only=True),
            "inactive": RuleService.count_rules(db, active_only=False) - RuleService.count_rules(db, active_only=True),
        },
        "facts": {
            "total": FactService.count_facts(db, persistent_only=False),
            "persistent": FactService.count_facts(db, persistent_only=True),
            "temporary": FactService.count_facts(db, persistent_only=False) - FactService.count_facts(db, persistent_only=True),
        },
    }
