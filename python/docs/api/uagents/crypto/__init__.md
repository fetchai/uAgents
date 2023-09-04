<a id="src.uagents.crypto.__init__"></a>

# src.uagents.crypto.`__`init`__`

<a id="src.uagents.crypto.__init__.Identity"></a>

## Identity Objects

```python
class Identity()
```

An identity is a cryptographic keypair that can be used to sign messages.

<a id="src.uagents.crypto.__init__.Identity.__init__"></a>

#### `__`init`__`

```python
def __init__(signing_key: ecdsa.SigningKey)
```

Create a new identity from a signing key.

<a id="src.uagents.crypto.__init__.Identity.from_seed"></a>

#### from`_`seed

```python
@staticmethod
def from_seed(seed: str, index: int) -> "Identity"
```

Create a new identity from a seed and index.

<a id="src.uagents.crypto.__init__.Identity.generate"></a>

#### generate

```python
@staticmethod
def generate() -> "Identity"
```

Generate a random new identity.

<a id="src.uagents.crypto.__init__.Identity.from_string"></a>

#### from`_`string

```python
@staticmethod
def from_string(private_key_hex: str) -> "Identity"
```

Create a new identity from a private key.

<a id="src.uagents.crypto.__init__.Identity.private_key"></a>

#### private`_`key

```python
@property
def private_key() -> str
```

Property to access the private key of the identity.

<a id="src.uagents.crypto.__init__.Identity.address"></a>

#### address

```python
@property
def address() -> str
```

Property to access the address of the identity.

<a id="src.uagents.crypto.__init__.Identity.sign"></a>

#### sign

```python
def sign(data: bytes) -> str
```

Sign the provided data.

<a id="src.uagents.crypto.__init__.Identity.sign_digest"></a>

#### sign`_`digest

```python
def sign_digest(digest: bytes) -> str
```

Sign the provided digest.

<a id="src.uagents.crypto.__init__.Identity.sign_registration"></a>

#### sign`_`registration

```python
def sign_registration(contract_address: str, sequence: int) -> str
```

Sign the registration data for the Almanac contract.

<a id="src.uagents.crypto.__init__.Identity.verify_digest"></a>

#### verify`_`digest

```python
@staticmethod
def verify_digest(address: str, digest: bytes, signature: str) -> bool
```

Verify that the signature is correct for the provided signer address and digest.

