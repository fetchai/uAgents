<a id="src.uagents.network"></a>

# src.uagents.network

Network and Contracts.

<a id="src.uagents.network.get_ledger"></a>

#### get`_`ledger

```python
def get_ledger() -> LedgerClient
```

Get the Ledger client.

**Returns**:

- `LedgerClient` - The Ledger client instance.

<a id="src.uagents.network.get_faucet"></a>

#### get`_`faucet

```python
def get_faucet() -> FaucetApi
```

Get the Faucet API instance.

**Returns**:

- `FaucetApi` - The Faucet API instance.

<a id="src.uagents.network.wait_for_tx_to_complete"></a>

#### wait`_`for`_`tx`_`to`_`complete

```python
async def wait_for_tx_to_complete(
        tx_hash: str,
        timeout: Optional[timedelta] = None,
        poll_period: Optional[timedelta] = None) -> TxResponse
```

Wait for a transaction to complete on the Ledger.

**Arguments**:

- `tx_hash` _str_ - The hash of the transaction to monitor.
- `timeout` _Optional[timedelta], optional_ - The maximum time to wait for
  the transaction to complete. Defaults to None.
- `poll_period` _Optional[timedelta], optional_ - The time interval to poll
  the Ledger for the transaction status. Defaults to None.
  

**Returns**:

- `TxResponse` - The response object containing the transaction details.

<a id="src.uagents.network.AlmanacContract"></a>

## AlmanacContract Objects

```python
class AlmanacContract(LedgerContract)
```

A class representing the Almanac contract for agent registration.

This class provides methods to interact with the Almanac contract, including
checking if an agent is registered, retrieving the expiry height of an agent's
registration, and getting the endpoints associated with an agent's registration.

<a id="src.uagents.network.AlmanacContract.is_registered"></a>

#### is`_`registered

```python
def is_registered(address: str) -> bool
```

Check if an agent is registered in the Almanac contract.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `bool` - True if the agent is registered, False otherwise.

<a id="src.uagents.network.AlmanacContract.get_expiry"></a>

#### get`_`expiry

```python
def get_expiry(address: str) -> int
```

Get the expiry height of an agent's registration.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `int` - The expiry height of the agent's registration.

<a id="src.uagents.network.AlmanacContract.get_endpoints"></a>

#### get`_`endpoints

```python
def get_endpoints(address: str)
```

Get the endpoints associated with an agent's registration.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `Any` - The endpoints associated with the agent's registration.

<a id="src.uagents.network.AlmanacContract.get_protocols"></a>

#### get`_`protocols

```python
def get_protocols(address: str)
```

Get the protocols associated with an agent's registration.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `Any` - The protocols associated with the agent's registration.

<a id="src.uagents.network.AlmanacContract.register"></a>

#### register

```python
async def register(ledger: LedgerClient, wallet: LocalWallet,
                   agent_address: str, protocols: List[str],
                   endpoints: List[Dict[str, Any]], signature: str)
```

Register an agent with the Almanac contract.

**Arguments**:

- `ledger` _LedgerClient_ - The Ledger client.
- `wallet` _LocalWallet_ - The agent's wallet.
- `agent_address` _str_ - The agent's address.
- `protocols` _List[str]_ - List of protocols.
- `endpoints` _List[Dict[str, Any]]_ - List of endpoint dictionaries.
- `signature` _str_ - The agent's signature.

<a id="src.uagents.network.AlmanacContract.get_sequence"></a>

#### get`_`sequence

```python
def get_sequence(address: str) -> int
```

Get the agent's sequence number for Almanac registration.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `int` - The agent's sequence number.

<a id="src.uagents.network.get_almanac_contract"></a>

#### get`_`almanac`_`contract

```python
def get_almanac_contract() -> AlmanacContract
```

Get the AlmanacContract instance.

**Returns**:

- `AlmanacContract` - The AlmanacContract instance.

<a id="src.uagents.network.NameServiceContract"></a>

## NameServiceContract Objects

```python
class NameServiceContract(LedgerContract)
```

A class representing the NameService contract for managing domain names and ownership.

This class provides methods to interact with the NameService contract, including
checking name availability, checking ownership, querying domain public status,
obtaining registration transaction details, and registering a name within a domain.

<a id="src.uagents.network.NameServiceContract.is_name_available"></a>

#### is`_`name`_`available

```python
def is_name_available(name: str, domain: str)
```

Check if a name is available within a domain.

**Arguments**:

- `name` _str_ - The name to check.
- `domain` _str_ - The domain to check within.
  

**Returns**:

- `bool` - True if the name is available, False otherwise.

<a id="src.uagents.network.NameServiceContract.is_owner"></a>

#### is`_`owner

```python
def is_owner(name: str, domain: str, wallet_address: str)
```

Check if the provided wallet address is the owner of a name within a domain.

**Arguments**:

- `name` _str_ - The name to check ownership for.
- `domain` _str_ - The domain to check within.
- `wallet_address` _str_ - The wallet address to check ownership against.
  

**Returns**:

- `bool` - True if the wallet address is the owner, False otherwise.

<a id="src.uagents.network.NameServiceContract.is_domain_public"></a>

#### is`_`domain`_`public

```python
def is_domain_public(domain: str)
```

Check if a domain is public.

**Arguments**:

- `domain` _str_ - The domain to check.
  

**Returns**:

- `bool` - True if the domain is public, False otherwise.

<a id="src.uagents.network.NameServiceContract.get_registration_tx"></a>

#### get`_`registration`_`tx

```python
def get_registration_tx(name: str, wallet_address: str, agent_address: str,
                        domain: str)
```

Get the registration transaction for registering a name within a domain.

**Arguments**:

- `name` _str_ - The name to be registered.
- `wallet_address` _str_ - The wallet address initiating the registration.
- `agent_address` _str_ - The address of the agent.
- `domain` _str_ - The domain in which the name is registered.
  

**Returns**:

- `Optional[Transaction]` - The registration transaction, or None if the name is not
  available or not owned by the wallet address.

<a id="src.uagents.network.NameServiceContract.register"></a>

#### register

```python
async def register(ledger: LedgerClient, wallet: LocalWallet,
                   agent_address: str, name: str, domain: str)
```

Register a name within a domain using the NameService contract.

**Arguments**:

- `ledger` _LedgerClient_ - The Ledger client.
- `wallet` _LocalWallet_ - The wallet of the agent.
- `agent_address` _str_ - The address of the agent.
- `name` _str_ - The name to be registered.
- `domain` _str_ - The domain in which the name is registered.

<a id="src.uagents.network.get_name_service_contract"></a>

#### get`_`name`_`service`_`contract

```python
def get_name_service_contract() -> NameServiceContract
```

Get the NameServiceContract instance.

**Returns**:

- `NameServiceContract` - The NameServiceContract instance.

