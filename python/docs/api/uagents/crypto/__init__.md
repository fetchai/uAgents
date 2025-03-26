

# src.uagents.crypto.__init__



#### sign_registration[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/crypto/__init__.py#L8)
```python
def sign_registration(identity: Identity, contract_address: str,
                      timestamp: int, wallet_address: str) -> str
```

Sign the registration data for the Almanac contract.



#### sign_arbitrary[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/crypto/__init__.py#L23)
```python
def sign_arbitrary(identity: Identity, data: bytes) -> tuple[str, str]
```

Sign arbitrary data with the given identity.

Only used for wallet messaging.

