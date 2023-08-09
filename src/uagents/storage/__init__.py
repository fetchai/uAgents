import json
import os
from typing import Any, Optional
from typing import Tuple
from cosmpy.aerial.wallet import PrivateKey
from uagents.crypto import Identity


class KeyValueStore:
    """
    A simple key-value store implementation for data storage.

    Attributes:
        _data (dict): The internal data storage dictionary.
        _name (str): The name associated with the store.
        _path (str): The file path where the store data is stored.

    Methods:
        __init__: Initialize the KeyValueStore instance.
        get: Get the value associated with a key from the store.
        has: Check if a key exists in the store.
        set: Set a value associated with a key in the store.
        remove: Remove a key and its associated value from the store.
        clear: Clear all data from the store.
        _load: Load data from the file into the store.
        _save: Save the store data to the file.

    """

    def __init__(self, name: str, cwd: str = None):
        """
        Initialize the KeyValueStore instance.

        Args:
            name (str): The name associated with the store.
            cwd (str, optional): The current working directory. Defaults to None.

        """
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


def load_all_keys() -> dict:
    """
    Load all private keys from the private keys file.

    Returns:
        dict: A dictionary containing loaded private keys.

    """
    private_keys_path = os.path.join(os.getcwd(), "private_keys.json")
    if os.path.exists(private_keys_path):
        with open(private_keys_path, encoding="utf-8") as load_file:
            return json.load(load_file)
    return {}


def save_private_keys(name: str, identity_key: str, wallet_key: str):
    """
    Save private keys to the private keys file.

    Args:
        name (str): The name associated with the private keys.
        identity_key (str): The identity private key.
        wallet_key (str): The wallet private key.

    """
    private_keys = load_all_keys()
    private_keys[name] = {"identity_key": identity_key, "wallet_key": wallet_key}

    private_keys_path = os.path.join(os.getcwd(), "private_keys.json")
    with open(private_keys_path, "w", encoding="utf-8") as write_file:
        json.dump(private_keys, write_file, indent=4)


def get_or_create_private_keys(name: str) -> Tuple[str, str]:
    """
    Get or create private keys associated with a name.

    Args:
        name (str): The name associated with the private keys.

    Returns:
        Tuple[str, str]: A tuple containing the identity key and wallet key.

    """
    keys = load_all_keys()
    if name in keys.keys():
        private_keys = keys.get(name)
        return private_keys["identity_key"], private_keys["wallet_key"]

    identity_key = Identity.generate().private_key
    wallet_key = PrivateKey().private_key

    save_private_keys(name, identity_key, PrivateKey().private_key)
    return identity_key, wallet_key
