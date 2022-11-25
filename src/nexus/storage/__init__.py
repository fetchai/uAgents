import json
import os
from typing import Any, Optional
from cosmpy.aerial.wallet import PrivateKey
import bech32


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


def load_keys() -> dict:
    sk_path = os.path.join(os.getcwd(), "private_keys.json")
    if os.path.exists(sk_path):
        with open(sk_path, encoding="utf-8") as load_file:
            return json.load(load_file)
    return {}


def save_key(name: str, key: str):
    keys = load_keys()

    if name not in keys.keys():
        keys[name] = {"instance_key": "", "wallet_key": ""}

    if isinstance(key, bytes):
        instance_key = _encode_bech32("agent", key)
        keys.get(name)["instance_key"] = instance_key

    elif isinstance(key, str):
        keys.get(name)["wallet_key"] = key
    else:
        assert False

    sk_path = os.path.join(os.getcwd(), "private_keys.json")
    with open(sk_path, "w", encoding="utf-8") as write_file:
        json.dump(keys, write_file, indent=4)


def query_key(name: str, key_type: str) -> str:
    keys = load_keys()
    if name in keys.keys():
        return keys.get(name)[key_type]
    return ""


def get_wallet_key(name: str) -> PrivateKey:
    saved_key = query_key(name, "wallet_key")
    if saved_key:
        return PrivateKey(saved_key)
    key = PrivateKey()
    save_key(name, key.private_key)
    return key


def _encode_bech32(prefix: str, value: bytes) -> str:
    value_base5 = bech32.convertbits(value, 8, 5)
    return bech32.bech32_encode(prefix, value_base5)
