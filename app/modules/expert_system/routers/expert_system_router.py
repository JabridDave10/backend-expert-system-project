import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from fastapi.responses import FileResponse

from app.modules.expert_system.schemas.recommendation_request_dto import RecommendationRequest
from app.modules.expert_system.schemas.recommendation_response_dto import RecommendationResponse
from app.modules.expert_system.schemas.constraints_request_dto import DiagnoseRequest
from app.modules.expert_system.services.expert_engine import ExpertEngine
from app.modules.expert_system.services.rawg_client import RawgClient
from app.modules.expert_system.services.catalog_store import CatalogStore

router = APIRouter(prefix="/expert-system", tags=["expert-system"])

_engine = ExpertEngine()
_store = CatalogStore(file_path="app_data/catalog_games.json")


@router.get("/ping")
async def ping():
    return {"status": "ok"}


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_games(payload: RecommendationRequest) -> RecommendationResponse:
    items, rules = _engine.recommend(payload.preferences, payload.limit)
    return RecommendationResponse(recommendations=items, rules_applied=rules, total=len(items))


@router.post("/sync")
async def sync_catalog(max_pages: int = 5, page_size: int = 40, genres: Optional[str] = None, platforms: Optional[str] = None, ordering: Optional[str] = "-rating"):
    try:
        client = RawgClient()
        filters = {}
        if genres:
            filters["genres"] = genres
        if platforms:
            filters["platforms"] = platforms
        if ordering:
            filters["ordering"] = ordering
        games = client.fetch_all_games(max_pages=max_pages, page_size=page_size, **filters)
        # Guardar RAW en cache
        _store.save(games)
        # Recargar motor
        _engine.reload_from_cache(_store.load())
        return {"downloaded": len(games)}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@router.get("/catalog-size")
async def catalog_size():
    data = _store.load()
    return {"catalog_size": len(data)}


@router.get("/download-catalog")
async def download_catalog(api_key: str, max_pages: int = 5, page_size: int = 40, genres: Optional[str] = None, platforms: Optional[str] = None, ordering: Optional[str] = "-rating"):
    """Descarga el catálogo desde RAWG con la api_key suministrada y devuelve el JSON como archivo."""
    try:
        client = RawgClient(api_key=api_key)
        filters = {}
        if genres:
            filters["genres"] = genres
        if platforms:
            filters["platforms"] = platforms
        if ordering:
            filters["ordering"] = ordering
        games = client.fetch_all_games(max_pages=max_pages, page_size=page_size, **filters)
        _store.save(games)
        _engine.reload_from_cache(_store.load())
        return FileResponse(path=_store.file_path, media_type="application/json", filename="catalog_games.json")
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@router.post("/to-ndjson")
async def convert_to_ndjson():
    ndjson_path = "app_data/catalog_games.ndjson"
    count = _store.to_ndjson(ndjson_path)
    return {"converted": count, "path": ndjson_path}


@router.get("/search-ndjson")
async def search_ndjson(
    q: Optional[str] = Query(default=None),
    page: int = 1,
    page_size: int = 20,
    genre: Optional[str] = None,
    platform: Optional[str] = None,
    min_rating: Optional[float] = None,
    min_metacritic: Optional[int] = None,
    released_from: Optional[str] = None,  # YYYY-MM-DD
    released_to: Optional[str] = None,    # YYYY-MM-DD
    only_released: bool = False,
    multiplayer: Optional[bool] = None,
    age_max: Optional[int] = None,
):
    ndjson_path = "app_data/catalog_games.ndjson"
    # Si no existe NDJSON, lo creamos on-demand para no cargar el JSON en memoria
    if not os.path.exists(ndjson_path):
        try:
            _store.to_ndjson(ndjson_path)
        except Exception as ex:
            raise HTTPException(status_code=500, detail=f"No se pudo crear NDJSON: {ex}")
    start = max(0, (page - 1) * page_size)
    end = start + page_size
    results: List[dict] = []
    emitted = 0
    # Mapa ESRB a edad
    age_map = {
        "Everyone": 6,
        "Everyone 10+": 10,
        "Teen": 13,
        "Mature": 17,
        "Adults Only": 21,
    }
    # Parse fechas
    def parse_date(s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            return None
    d_from = parse_date(released_from)
    d_to = parse_date(released_to)

    matched = 0
    for item in _store.iter_ndjson(ndjson_path):
        # Derivados RAWG → campos del sistema experto
        esrb = None
        if isinstance(item.get("esrb_rating"), dict):
            esrb = item.get("esrb_rating", {}).get("name")
        age_rating_val = age_map.get(esrb, 12 if esrb else 12)
        tags = item.get("tags") or []
        tag_names = [t.get("name", "").lower() for t in tags if isinstance(t, dict)]
        is_multiplayer = any("multiplayer" in t for t in tag_names)
        # Normalización de listas
        genres = item.get("genres") or []
        genres_names = [g.get("name") if isinstance(g, dict) else g for g in genres]
        platforms = item.get("platforms") or []
        platforms_names = [
            (p.get("platform") or {}).get("name") if isinstance(p, dict) else p for p in platforms
        ]
        title = item.get("title") or item.get("name") or ""
        released = item.get("released")
        rating_val = float(item.get("rating") or 0.0)
        metacritic_val = int(item.get("metacritic") or 0) if item.get("metacritic") is not None else 0

        # Exclusión de contenido sensible: si age_max < 18, filtrar NSFW/sex/violence/gore
        if age_max is not None and age_max < 18:
            sensitive = {"nsfw", "nudity", "sexual content", "sexual-content", "hentai", "porn", "erotic", "mature", "violence", "violent", "gore"}
            if any(any(s in t for s in sensitive) for t in tag_names):
                continue

        # Filtros
        if q and q.lower() not in title.lower():
            continue
        if genre:
            if not any(genre.lower() == (g or "").lower() for g in genres_names):
                continue
        if platform:
            if not any(platform.lower() == (p or "").lower() for p in platforms_names):
                continue
        if min_rating is not None and rating_val < min_rating:
            continue
        if min_metacritic is not None and metacritic_val < min_metacritic:
            continue
        if only_released:
            if item.get("tba") or not released:
                continue
        if d_from or d_to:
            rd = parse_date(released)
            if d_from and (rd is None or rd < d_from):
                continue
            if d_to and (rd is None or rd > d_to):
                continue
        if multiplayer is not None and is_multiplayer != multiplayer:
            continue
        if age_max is not None and age_rating_val > age_max:
            continue

        # Pasa filtros → conteo para paginación y proyección
        if matched >= start and matched < end:
            projected = {
                "id": item.get("id"),
                "title": title,
                "released": released,
                "rating": rating_val,
                "metacritic": metacritic_val,
                "genres": genres_names,
                "platforms": platforms_names,
                "age_rating": age_rating_val,
                "multiplayer": is_multiplayer,
                "playtime_hours": int(item.get("playtime") or 0),
                "price": 0.0,
                "difficulty": "normal",
                "background_image": item.get("background_image"),
                "tba": item.get("tba"),
            }
            results.append(projected)
            emitted += 1
            if emitted >= page_size:
                break
        matched += 1

    return {"page": page, "page_size": page_size, "items": results, "count": len(results)}


@router.post("/diagnose")
async def diagnose(req: DiagnoseRequest):
    ndjson_path = "app_data/catalog_games.ndjson"
    if not os.path.exists(ndjson_path):
        try:
            _store.to_ndjson(ndjson_path)
        except Exception as ex:
            raise HTTPException(status_code=500, detail=f"No se pudo crear NDJSON: {ex}")
    rules_log: List[str] = []
    matches: List[Dict[str, Any]] = []
    examined = 0

    # Normalizar paginación
    page_size = req.page_size or 12
    if req.limit is not None:
        page_size = req.limit
    page = req.page or 1
    start = (page - 1) * page_size
    end = start + page_size

    # Conjunto de tags sensibles para menores
    sensitive_tags = {"nsfw", "nudity", "sexual content", "sexual-content", "hentai", "porn", "erotic", "mature", "violence", "violent", "gore"}

    def log(rule: str, before: int, after: int):
        rules_log.append(f"{rule}: {before}->{after}")

    passed = 0
    for item in _store.iter_ndjson(ndjson_path):
        examined += 1
        keep = True
        # Normalizar
        genres = [g.get("name") if isinstance(g, dict) else g for g in (item.get("genres") or [])]
        platforms = [
            (p.get("platform") or {}).get("name") if isinstance(p, dict) else p for p in (item.get("platforms") or [])
        ]
        tags = [t.get("name", "").lower() for t in (item.get("tags") or []) if isinstance(t, dict)]
        title = item.get("name") or item.get("title") or ""
        released = item.get("released")
        playtime_hours = int(item.get("playtime") or 0)
        esrb = (item.get("esrb_rating") or {}).get("name") if item.get("esrb_rating") else None
        age_map = {
            "Everyone": 6,
            "Everyone 10+": 10,
            "Teen": 13,
            "Mature": 17,
            "Adults Only": 21,
        }
        age_rating = age_map.get(esrb, 12 if esrb else 12)

        # Reglas sensibles por edad o preferencia de violencia
        if keep and req.content.age_max is not None and req.content.age_max < 18:
            if any(any(s in t for s in sensitive_tags) for t in tags):
                keep = False
        if keep and req.content.allow_violence is False:
            if any(any(s in t for s in sensitive_tags) for t in tags):
                keep = False
        if keep and req.content.age_max is not None and age_rating > req.content.age_max:
            keep = False
        if keep and req.content.multiplayer_required is not None:
            is_mp = any("multiplayer" in t for t in tags)
            if req.content.multiplayer_required and not is_mp:
                keep = False
            if not req.content.multiplayer_required and is_mp:
                keep = False
        if keep and req.preferences.exclude_genres:
            if any(eg.lower() in [g.lower() for g in genres] for eg in req.preferences.exclude_genres):
                keep = False
        if keep and req.preferences.include_genres:
            if not any(ig.lower() in [g.lower() for g in genres] for ig in req.preferences.include_genres):
                keep = False
        if keep and req.hardware.platform:
            if req.hardware.platform.lower() not in [p.lower() for p in platforms]:
                keep = False
        if keep and req.time.max_playtime_hours is not None and playtime_hours > req.time.max_playtime_hours:
            keep = False
        if keep and req.content.offline_required:
            if any("online" in t for t in tags):
                keep = False
        # Precio: no aplicable (RAWG no da precio)

        if not keep:
            continue

        if passed >= start and passed < end:
            matches.append({
                "id": item.get("id"),
                "title": title,
                "released": released,
                "genres": genres,
                "platforms": platforms,
                "age_rating": age_rating,
                "playtime_hours": playtime_hours,
                "background_image": item.get("background_image"),
            })
            if len(matches) >= page_size:
                break
        passed += 1

    return {
        "page": page,
        "page_size": page_size,
        "matched": len(matches),
        "examined": examined,
        "items": matches,
    }
