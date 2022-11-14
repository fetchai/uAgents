import json
import os
from typing import Any, Optional


class KeyValueStore:
    def __init__(self, name: str, cwd: str = None):
        self._data = {}
        self._name = name or "my"

        cwd = cwd or os.getcwd()
        self._path = os.path.join(cwd, f"{self._name}_data.json")

        if os.path.isfile(self._path):
            self._load()

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    def has(self, key: str) -> bool:
        return key in self._data

    def set(self, key: str, value: Any):
        self._data[key] = value
        self._save()

    def remove(self, key: str):
        if key in self._data:
            del self._data[key]
            self._save()

    def clear(self):
        self._data.clear()
        self._save()

    def _load(self):
        with open(self._path, "r", encoding="utf-8") as file:
            self._data = json.load(file)

    def _save(self):
        with open(self._path, "w", encoding="utf-8") as file:
            json.dump(self._data, file, ensure_ascii=False, indent=4)
