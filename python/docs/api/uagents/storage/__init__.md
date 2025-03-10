

# src.uagents.storage.__init__



## StorageAPI Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/storage/__init__.py#L11)

```python
class StorageAPI(ABC)
```

Interface for a key-value like storage system.



## KeyValueStore Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/storage/__init__.py#L35)

```python
class KeyValueStore(StorageAPI)
```

A simple key-value store implementation for data storage.

**Attributes**:

- `_data` _dict_ - The internal data storage dictionary.
- `_name` _str_ - The name associated with the store.
- `_path` _str_ - The file path where the store data is stored.
  

**Methods**:

- `__init__` - Initialize the KeyValueStore instance.
- `get` - Get the value associated with a key from the store.
- `has` - Check if a key exists in the store.
- `set` - Set a value associated with a key in the store.
- `remove` - Remove a key and its associated value from the store.
- `clear` - Clear all data from the store.
- `_load` - Load data from the file into the store.
- `_save` - Save the store data to the file.



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/storage/__init__.py#L55)
```python
def __init__(name: str, cwd: str | None = None)
```

Initialize the KeyValueStore instance.

**Arguments**:

- `name` _str_ - The name associated with the store.
- `cwd` _str | None_ - The current working directory. Defaults to None.



#### load_all_keys[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/storage/__init__.py#L100)
```python
def load_all_keys() -> dict
```

Load all private keys from the private keys file.

**Returns**:

- `dict` - A dictionary containing loaded private keys.



#### save_private_keys[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/storage/__init__.py#L114)
```python
def save_private_keys(name: str, identity_key: str, wallet_key: str) -> None
```

Save private keys to the private keys file.

**Arguments**:

- `name` _str_ - The name associated with the private keys.
- `identity_key` _str_ - The identity private key.
- `wallet_key` _str_ - The wallet private key.



#### get_or_create_private_keys[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/storage/__init__.py#L131)
```python
def get_or_create_private_keys(name: str) -> tuple[str, str]
```

Get or create private keys associated with a name.

**Arguments**:

- `name` _str_ - The name associated with the private keys.
  

**Returns**:

  tuple[str, str]: A tuple containing the identity key and wallet key.

