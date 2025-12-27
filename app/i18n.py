import os
import yaml


class Translator:
    def __init__(self):
        self._cache = {}

    def _load(self, lang: str) -> dict:
        if lang in self._cache:
            return self._cache[lang]

        base = os.path.dirname(__file__)
        path = os.path.join(base, "static", "i18n", f"{lang}.yaml")
        if not os.path.exists(path):
            self._cache[lang] = {}
            return {}

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._cache[lang] = data
        return data

    def t(self, lang: str, key: str) -> str:
        data = self._load(lang)
        cur = data
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return key
        return str(cur)
