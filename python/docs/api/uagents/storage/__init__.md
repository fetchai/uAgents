<a id="src.uagents.storage.__init__"></a>

# src.uagents.storage.`__`init`__`

<a id="src.uagents.storage.__init__.KeyValueStore"></a>

## KeyValueStore Objects

```python
class KeyValueStore()
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

<a id="src.uagents.storage.__init__.KeyValueStore.__init__"></a>

#### `__`init`__`

```python
def __init__(name: str, cwd: str = None)
```

Initialize the KeyValueStore instance.

**Arguments**:

- `name` _str_ - The name associated with the store.
- `cwd` _str, optional_ - The current working directory. Defaults to None.

<a id="src.uagents.storage.__init__.load_all_keys"></a>

#### load`_`all`_`keys

```python
def load_all_keys() -> dict
```

Load all private keys from the private keys file.

**Returns**:

- `dict` - A dictionary containing loaded private keys.

<a id="src.uagents.storage.__init__.save_private_keys"></a>

#### save`_`private`_`keys

```python
def save_private_keys(name: str, identity_key: str, wallet_key: str)
```

Save private keys to the private keys file.

**Arguments**:

- `name` _str_ - The name associated with the private keys.
- `identity_key` _str_ - The identity private key.
- `wallet_key` _str_ - The wallet private key.

<a id="src.uagents.storage.__init__.get_or_create_private_keys"></a>

#### get`_`or`_`create`_`private`_`keys

```python
def get_or_create_private_keys(name: str) -> Tuple[str, str]
```

Get or create private keys associated with a name.

**Arguments**:

- `name` _str_ - The name associated with the private keys.
  

**Returns**:

  Tuple[str, str]: A tuple containing the identity key and wallet key.

