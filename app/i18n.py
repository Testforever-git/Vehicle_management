import os
import yaml


class Translator:
    def __init__(self):
        self._cache = {}

    def _load(self, page: str) -> dict:
        if page in self._cache:
            return self._cache[page]

        base = os.path.dirname(__file__)
        path = os.path.join(base, "static", "i18n", f"{page}.yaml")
        if not os.path.exists(path):
            self._cache[page] = {}
            return {}

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._cache[page] = data
        return data

    def t(self, lang: str, key: str) -> str:
        parts = key.split(".")
        if len(parts) < 2:
            return key

        page, rest = parts[0], parts[1:]
        data = self._load(page)
        cur = data.get(lang, {})
        for part in rest:
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return key
        return str(cur)
