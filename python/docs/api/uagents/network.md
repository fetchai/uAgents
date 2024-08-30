<a id="src.uagents.network"></a>

# src.uagents.network

Network and Contracts.

<a id="src.uagents.network.InsufficientFundsError"></a>

## InsufficientFundsError Objects

```python
class InsufficientFundsError(Exception)
```

Raised when an agent has insufficient funds for a transaction.

<a id="src.uagents.network.get_ledger"></a>

#### get`_`ledger

```python
def get_ledger(test: bool = True) -> LedgerClient
```

Get the Ledger client.

**Arguments**:

- `test` _bool_ - Whether to use the testnet or mainnet. Defaults to True.
  

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

<a id="src.uagents.network.add_testnet_funds"></a>

#### add`_`testnet`_`funds

```python
def add_testnet_funds(wallet_address: str)
```

Add testnet funds to the provided wallet address.

**Arguments**:

- `wallet_address` _str_ - The wallet address to add funds to.

<a id="src.uagents.network.parse_record_config"></a>

#### parse`_`record`_`config

```python
def parse_record_config(
    record: Optional[Union[str, List[str], Dict[str, dict]]]
) -> Optional[List[Dict[str, Any]]]
```

Parse the user-provided record configuration.

**Returns**:

  Optional[List[Dict[str, Any]]]: The parsed record configuration in correct format.

<a id="src.uagents.network.wait_for_tx_to_complete"></a>

#### wait`_`for`_`tx`_`to`_`complete

```python
async def wait_for_tx_to_complete(
        tx_hash: str,
        ledger: LedgerClient,
        timeout: Optional[timedelta] = None,
        poll_period: Optional[timedelta] = None) -> TxResponse
```

Wait for a transaction to complete on the Ledger.

**Arguments**:

- `tx_hash` _str_ - The hash of the transaction to monitor.
- `ledger` _LedgerClient_ - The Ledger client to poll.
- `timeout` _Optional[timedelta], optional_ - The maximum time to wait.
  the transaction to complete. Defaults to None.
- `poll_period` _Optional[timedelta], optional_ - The time interval to poll
  

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

<a id="src.uagents.network.AlmanacContract.query_contract"></a>

#### query`_`contract

```python
def query_contract(query_msg: Dict[str, Any]) -> Any
```

Execute a query with additional checks and error handling.

**Arguments**:

- `query_msg` _Dict[str, Any]_ - The query message.
  

**Returns**:

- `Any` - The query response.
  

**Raises**:

- `RuntimeError` - If the contract address is not set or the query fails.

<a id="src.uagents.network.AlmanacContract.get_contract_version"></a>

#### get`_`contract`_`version

```python
def get_contract_version() -> str
```

Get the version of the contract.

**Returns**:

- `str` - The version of the contract.

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
def get_endpoints(address: str) -> List[AgentEndpoint]
```

Get the endpoints associated with an agent's registration.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `List[AgentEndpoint]` - The endpoints associated with the agent's registration.

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
                   endpoints: List[AgentEndpoint], signature: str)
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
def get_almanac_contract(test: bool = True) -> AlmanacContract
```

Get the AlmanacContract instance.

**Arguments**:

- `test` _bool_ - Whether to use the testnet or mainnet. Defaults to True.
  

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

<a id="src.uagents.network.NameServiceContract.query_contract"></a>

#### query`_`contract

```python
def query_contract(query_msg: Dict[str, Any]) -> Any
```

Execute a query with additional checks and error handling.

**Arguments**:

- `query_msg` _Dict[str, Any]_ - The query message.
  

**Returns**:

- `Any` - The query response.
  

**Raises**:

- `RuntimeError` - If the contract address is not set or the query fails.

<a id="src.uagents.network.NameServiceContract.is_name_available"></a>

#### is`_`name`_`available

```python
def is_name_available(name: str, domain: str) -> bool
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
def is_owner(name: str, domain: str, wallet_address: str) -> bool
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
def is_domain_public(domain: str) -> bool
```

Check if a domain is public.

**Arguments**:

- `domain` _str_ - The domain to check.
  

**Returns**:

- `bool` - True if the domain is public, False otherwise.

<a id="src.uagents.network.NameServiceContract.get_previous_records"></a>

#### get`_`previous`_`records

```python
def get_previous_records(name: str, domain: str)
```

Retrieve the previous records for a given name within a specified domain.

**Arguments**:

- `name` _str_ - The name whose records are to be retrieved.
- `domain` _str_ - The domain within which the name is registered.
  

**Returns**:

  A list of dictionaries, where each dictionary contains
  details of a record associated with the given name.

<a id="src.uagents.network.NameServiceContract.get_registration_tx"></a>

#### get`_`registration`_`tx

```python
def get_registration_tx(name: str, wallet_address: Address,
                        agent_records: Union[List[Dict[str, Any]],
                                             str], domain: str, test: bool)
```

Get the registration transaction for registering a name within a domain.

**Arguments**:

- `name` _str_ - The name to be registered.
- `wallet_address` _str_ - The wallet address initiating the registration.
- `agent_address` _str_ - The address of the agent.
- `domain` _str_ - The domain in which the name is registered.
- `test` _bool_ - The agent type
  

**Returns**:

- `Optional[Transaction]` - The registration transaction, or None if the name is not
  available or not owned by the wallet address.

<a id="src.uagents.network.NameServiceContract.register"></a>

#### register

```python
async def register(ledger: LedgerClient,
                   wallet: LocalWallet,
                   agent_records: Optional[Union[str, List[str], Dict[str,
                                                                      dict]]],
                   name: str,
                   domain: str,
                   overwrite: bool = True)
```

Register a name within a domain using the NameService contract.

**Arguments**:

- `ledger` _LedgerClient_ - The Ledger client.
- `wallet` _LocalWallet_ - The wallet of the agent.
- `agent_address` _str_ - The address of the agent.
- `name` _str_ - The name to be registered.
- `domain` _str_ - The domain in which the name is registered.
- `overwrite` _bool, optional_ - Specifies whether to overwrite any existing
  addresses registered to the domain. If False, the address will be
  appended to the previous records. Defaults to True.

<a id="src.uagents.network.NameServiceContract.unregister"></a>

#### unregister

```python
async def unregister(name: str, domain: str, wallet: LocalWallet)
```

Unregister a name within a domain using the NameService contract.

**Arguments**:

- `name` _str_ - The name to be unregistered.
- `domain` _str_ - The domain in which the name is registered.
- `wallet` _LocalWallet_ - The wallet of the agent.

<a id="src.uagents.network.get_name_service_contract"></a>

#### get`_`name`_`service`_`contract

```python
def get_name_service_contract(test: bool = True) -> NameServiceContract
```

Get the NameServiceContract instance.

**Arguments**:

- `test` _bool_ - Whether to use the testnet or mainnet. Defaults to True.
  

**Returns**:

- `NameServiceContract` - The NameServiceContract instance.

