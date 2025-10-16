import http.client
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode
import os


class RawgClient:
    BASE_HOST = "api.rawg.io"
    BASE_PATH = "/api"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("RAWG_API_KEY")
        if not self.api_key:
            raise ValueError("RAWG_API_KEY no configurada en entorno")

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params = dict(params or {})
        params["key"] = self.api_key
        query = urlencode(params, doseq=True)
        full_path = f"{self.BASE_PATH}{path}?{query}"
        conn = http.client.HTTPSConnection(self.BASE_HOST, timeout=30)
        try:
            conn.request("GET", full_path)
            resp = conn.getresponse()
            raw = resp.read()
            if resp.status != 200:
                raise RuntimeError(f"RAWG error {resp.status}: {raw[:200].decode(errors='ignore')}")
            return json.loads(raw.decode("utf-8"))
        finally:
            conn.close()

    def list_games(self, *, page: int = 1, page_size: int = 40, **filters: Any) -> Dict[str, Any]:
        params = {"page": page, "page_size": page_size}
        params.update(filters)
        return self._get("/games", params)

    def fetch_all_games(self, *, max_pages: int = 50, page_size: int = 40, **filters: Any) -> List[Dict[str, Any]]:
        """Descarga paginada hasta max_pages. Ojo: traer "todo" puede ser enorme; controla límites."""
        results: List[Dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            data = self.list_games(page=page, page_size=page_size, **filters)
            batch = data.get("results", [])
            results.extend(batch)
            next_url = data.get("next")
            if not next_url or not batch:
                break
            page += 1
        return results

