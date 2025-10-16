import json
import os
from typing import List, Dict, Any, Iterable


class CatalogStore:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def save(self, items: List[Dict[str, Any]]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False)

    def load(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def to_ndjson(self, ndjson_path: str) -> int:
        """Convierte el JSON de lista a NDJSON (una línea por juego). Devuelve cantidad convertida."""
        data = self.load()
        count = 0
        with open(ndjson_path, "w", encoding="utf-8") as out:
            for item in data:
                out.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += 1
        return count

    def iter_ndjson(self, ndjson_path: str) -> Iterable[Dict[str, Any]]:
        if not os.path.exists(ndjson_path):
            return []
        def generator():
            with open(ndjson_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        return generator()

