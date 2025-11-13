"""
Router de administración para juegos y reglas
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.modules.expert_system.services.admin_game_service import AdminGameService
from app.modules.expert_system.services.admin_rule_service import AdminRuleService
from app.modules.expert_system.schemas.admin_game_dto import (
    GameCreateRequest,
    GameUpdateRequest,
    GameResponse,
    GameListResponse,
    GameDeleteResponse
)
from app.modules.expert_system.schemas.admin_rule_dto import (
    RuleCreateRequest,
    RuleUpdateRequest,
    RuleResponse,
    RuleListResponse,
    RuleDeleteResponse,
    RuleBulkDeleteRequest,
    RuleBulkDeleteResponse
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================
# ENDPOINTS DE GESTIÓN DE JUEGOS
# ============================================

@router.post("/games", response_model=GameResponse, status_code=201)
def create_game(
    game_data: GameCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo juego en el catálogo

    Args:
        game_data: Datos del juego a crear
        db: Sesión de base de datos

    Returns:
        Juego creado

    Raises:
        HTTPException 400: Si ya existe un juego con ese slug
    """
    try:
        game = AdminGameService.create_game(db, game_data)
        return game
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/games", response_model=GameListResponse)
def list_games(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    search: Optional[str] = Query(None, description="Buscar por nombre"),
    genre: Optional[str] = Query(None, description="Filtrar por género"),
    platform: Optional[str] = Query(None, description="Filtrar por plataforma"),
    db: Session = Depends(get_db)
):
    """
    Listar juegos con paginación y filtros

    Args:
        page: Número de página (comienza en 1)
        page_size: Cantidad de juegos por página
        search: Búsqueda por nombre (opcional)
        genre: Filtrar por género (opcional)
        platform: Filtrar por plataforma (opcional)
        db: Sesión de base de datos

    Returns:
        Lista paginada de juegos
    """
    games, total = AdminGameService.get_games_paginated(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        genre=genre,
        platform=platform
    )

    return GameListResponse(
        total=total,
        page=page,
        page_size=page_size,
        games=games
    )


@router.get("/games/search")
def search_games(
    q: str = Query(..., min_length=1, description="Texto a buscar"),
    limit: int = Query(10, ge=1, le=50, description="Límite de resultados"),
    db: Session = Depends(get_db)
):
    """
    Buscar juegos por nombre (para autocompletado)

    Args:
        q: Texto a buscar
        limit: Límite de resultados
        db: Sesión de base de datos

    Returns:
        Lista de juegos encontrados
    """
    games = AdminGameService.search_games(db, q, limit)
    return {"results": games}


@router.get("/games/stats")
def get_game_stats(db: Session = Depends(get_db)):
    """
    Obtener estadísticas de los juegos

    Args:
        db: Sesión de base de datos

    Returns:
        Estadísticas del catálogo de juegos
    """
    return AdminGameService.get_game_stats(db)


@router.get("/games/{game_id}", response_model=GameResponse)
def get_game(
    game_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener un juego por su ID

    Args:
        game_id: ID del juego
        db: Sesión de base de datos

    Returns:
        Datos del juego

    Raises:
        HTTPException 404: Si el juego no existe
    """
    game = AdminGameService.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return game


@router.put("/games/{game_id}", response_model=GameResponse)
def update_game(
    game_id: int,
    game_data: GameUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Actualizar un juego existente

    Args:
        game_id: ID del juego a actualizar
        game_data: Datos a actualizar
        db: Sesión de base de datos

    Returns:
        Juego actualizado

    Raises:
        HTTPException 404: Si el juego no existe
    """
    game = AdminGameService.update_game(db, game_id, game_data)
    if not game:
        raise HTTPException(status_code=404, detail="Juego no encontrado")
    return game


@router.delete("/games/{game_id}", response_model=GameDeleteResponse)
def delete_game(
    game_id: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar un juego

    Args:
        game_id: ID del juego a eliminar
        db: Sesión de base de datos

    Returns:
        Confirmación de eliminación

    Raises:
        HTTPException 404: Si el juego no existe
    """
    success = AdminGameService.delete_game(db, game_id)
    if not success:
        raise HTTPException(status_code=404, detail="Juego no encontrado")

    return GameDeleteResponse(
        success=True,
        message="Juego eliminado correctamente",
        game_id=game_id
    )


# ============================================
# ENDPOINTS DE GESTIÓN DE REGLAS
# ============================================

@router.post("/rules", response_model=RuleResponse, status_code=201)
def create_rule(
    rule_data: RuleCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Crear una nueva regla en el sistema experto

    Args:
        rule_data: Datos de la regla a crear
        db: Sesión de base de datos

    Returns:
        Regla creada

    Raises:
        HTTPException 400: Si ya existe una regla con ese nombre
    """
    try:
        rule = AdminRuleService.create_rule(db, rule_data)
        return rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules", response_model=RuleListResponse)
def list_rules(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=200, description="Tamaño de página"),
    search: Optional[str] = Query(None, description="Buscar por nombre o descripción"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    active_only: bool = Query(False, description="Solo reglas activas"),
    sort_by: str = Query("priority", description="Campo de ordenamiento"),
    sort_order: str = Query("desc", description="Orden (asc, desc)"),
    db: Session = Depends(get_db)
):
    """
    Listar reglas con paginación y filtros

    Args:
        page: Número de página (comienza en 1)
        page_size: Cantidad de reglas por página
        search: Búsqueda por nombre o descripción (opcional)
        category: Filtrar por categoría (opcional)
        active_only: Solo reglas activas (opcional)
        sort_by: Campo por el cual ordenar
        sort_order: Orden (asc, desc)
        db: Sesión de base de datos

    Returns:
        Lista paginada de reglas
    """
    rules, total = AdminRuleService.get_rules_paginated(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        active_only=active_only,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return RuleListResponse(
        total=total,
        page=page,
        page_size=page_size,
        rules=rules
    )


@router.get("/rules/categories")
def get_rule_categories(db: Session = Depends(get_db)):
    """
    Obtener lista de categorías de reglas

    Args:
        db: Sesión de base de datos

    Returns:
        Lista de categorías únicas
    """
    categories = AdminRuleService.get_rule_categories(db)
    return {"categories": categories}


@router.get("/rules/stats")
def get_rule_stats(db: Session = Depends(get_db)):
    """
    Obtener estadísticas de las reglas

    Args:
        db: Sesión de base de datos

    Returns:
        Estadísticas de las reglas
    """
    return AdminRuleService.get_rule_stats(db)


@router.get("/rules/{rule_id}", response_model=RuleResponse)
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener una regla por su ID

    Args:
        rule_id: ID de la regla
        db: Sesión de base de datos

    Returns:
        Datos de la regla

    Raises:
        HTTPException 404: Si la regla no existe
    """
    rule = AdminRuleService.get_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return rule


@router.put("/rules/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: int,
    rule_data: RuleUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Actualizar una regla existente

    Args:
        rule_id: ID de la regla a actualizar
        rule_data: Datos a actualizar
        db: Sesión de base de datos

    Returns:
        Regla actualizada

    Raises:
        HTTPException 404: Si la regla no existe
    """
    rule = AdminRuleService.update_rule(db, rule_id, rule_data)
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return rule


@router.delete("/rules/{rule_id}", response_model=RuleDeleteResponse)
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    Eliminar una regla

    Args:
        rule_id: ID de la regla a eliminar
        db: Sesión de base de datos

    Returns:
        Confirmación de eliminación

    Raises:
        HTTPException 404: Si la regla no existe
    """
    success = AdminRuleService.delete_rule(db, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Regla no encontrada")

    return RuleDeleteResponse(
        success=True,
        message="Regla eliminada correctamente",
        rule_id=rule_id
    )


@router.post("/rules/bulk-delete", response_model=RuleBulkDeleteResponse)
def bulk_delete_rules(
    request: RuleBulkDeleteRequest,
    db: Session = Depends(get_db)
):
    """
    Eliminar múltiples reglas

    Args:
        request: Lista de IDs de reglas a eliminar
        db: Sesión de base de datos

    Returns:
        Resultado de la eliminación masiva
    """
    deleted_count, failed_count = AdminRuleService.bulk_delete_rules(
        db,
        request.rule_ids
    )

    return RuleBulkDeleteResponse(
        success=failed_count == 0,
        message=f"Se eliminaron {deleted_count} reglas correctamente",
        deleted_count=deleted_count,
        failed_count=failed_count
    )


@router.post("/rules/{rule_id}/toggle", response_model=RuleResponse)
def toggle_rule_active(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    Alternar el estado activo/inactivo de una regla

    Args:
        rule_id: ID de la regla
        db: Sesión de base de datos

    Returns:
        Regla actualizada

    Raises:
        HTTPException 404: Si la regla no existe
    """
    rule = AdminRuleService.toggle_rule_active(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return rule


@router.post("/rules/{rule_id}/duplicate", response_model=RuleResponse)
def duplicate_rule(
    rule_id: int,
    new_name: str = Query(..., description="Nombre para la regla duplicada"),
    db: Session = Depends(get_db)
):
    """
    Duplicar una regla existente

    Args:
        rule_id: ID de la regla a duplicar
        new_name: Nombre para la nueva regla
        db: Sesión de base de datos

    Returns:
        Regla duplicada

    Raises:
        HTTPException 404: Si la regla no existe
        HTTPException 400: Si el nuevo nombre ya existe
    """
    try:
        rule = AdminRuleService.duplicate_rule(db, rule_id, new_name)
        if not rule:
            raise HTTPException(status_code=404, detail="Regla no encontrada")
        return rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
