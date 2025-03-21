

# src.uagents.network

Network and Contracts.



#### default_exp_backoff[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L54)
```python
def default_exp_backoff(retry: int) -> float
```

Generate a backoff time starting from 0.64 seconds and limited to ~32 seconds



#### block_polling_exp_backoff[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L61)
```python
def block_polling_exp_backoff(retry: int) -> float
```

Generate an exponential backoff that is designed for block polling. We keep the
same default exponential backoff, but it is clamped to the default query interval.



## InsufficientFundsError Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L70)

```python
class InsufficientFundsError(Exception)
```

Raised when an agent has insufficient funds for a transaction.



## BroadcastTimeoutError Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L74)

```python
class BroadcastTimeoutError(RuntimeError)
```

Raised when a transaction broadcast fails due to a timeout.



#### get_ledger[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L97)
```python
def get_ledger(network: AgentNetwork = "testnet") -> LedgerClient
```

Get the Ledger client.

**Arguments**:

- `network` _AgentNetwork, optional_ - The network to use. Defaults to "testnet".
  

**Returns**:

- `LedgerClient` - The Ledger client instance.



#### get_faucet[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L110)
```python
def get_faucet() -> FaucetApi
```

Get the Faucet API instance.

**Returns**:

- `FaucetApi` - The Faucet API instance.



#### add_testnet_funds[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L120)
```python
def add_testnet_funds(wallet_address: str) -> None
```

Add testnet funds to the provided wallet address.

**Arguments**:

- `wallet_address` _str_ - The wallet address to add funds to.



#### parse_record_config[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L132)
```python
def parse_record_config(
    record: str | list[str] | dict[str, dict] | None
) -> list[dict[str, Any]] | None
```

Parse the user-provided record configuration.

**Returns**:

  list[dict[str, Any]] | None: The parsed record configuration in correct format.



#### wait_for_tx_to_complete[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L155)
```python
async def wait_for_tx_to_complete(
        tx_hash: str,
        ledger: LedgerClient,
        *,
        poll_retries: int | None = None,
        poll_retry_delay: RetryDelayFunc | None = None) -> TxResponse
```

Wait for a transaction to complete on the Ledger.

**Arguments**:

- `tx_hash` _str_ - The hash of the transaction to monitor.
- `ledger` _LedgerClient_ - The Ledger client to poll.
- `poll_retries` _int, optional_ - The maximum number of retry attempts.
- `poll_retry_delay` _RetryDelayFunc, optional_ - The retry delay function,
  if not provided the default exponential backoff will be used.
  

**Returns**:

- `TxResponse` - The response object containing the transaction details.



## AlmanacContract Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L194)

```python
class AlmanacContract(LedgerContract)
```

A class representing the Almanac contract for agent registration.

This class provides methods to interact with the Almanac contract, including
checking if an agent is registered, retrieving the expiry height of an agent's
registration, and getting the endpoints associated with an agent's registration.



#### check_version[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L203)
```python
def check_version() -> bool
```

Check if the contract version supported by this version of uAgents matches the
deployed version.

**Returns**:

- `bool` - True if the contract version is supported, False otherwise.



#### query_contract[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L228)
```python
def query_contract(query_msg: dict[str, Any]) -> Any
```

Execute a query with additional checks and error handling.

**Arguments**:

- `query_msg` _dict[str, Any]_ - The query message.
  

**Returns**:

- `Any` - The query response.
  

**Raises**:

- `RuntimeError` - If the contract address is not set or the query fails.



#### get_contract_version[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L251)
```python
def get_contract_version() -> str
```

Get the version of the contract.

**Returns**:

- `str` - The version of the contract.



#### get_registration_fee[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L263)
```python
def get_registration_fee() -> int
```

Get the registration fee for the contract.

**Returns**:

- `int` - The registration fee.



#### is_registered[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L275)
```python
def is_registered(address: str) -> bool
```

Check if an agent is registered in the Almanac contract.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `bool` - True if the agent is registered, False otherwise.



#### registration_needs_update[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L290)
```python
def registration_needs_update(address: str, endpoints: list[AgentEndpoint],
                              protocols: list[str],
                              min_seconds_left: int) -> bool
```

Check if an agent's registration needs to be updated.

**Arguments**:

- `address` _str_ - The agent's address.
- `endpoints` _list[AgentEndpoint]_ - The agent's endpoints.
- `protocols` _list[str]_ - The agent's protocols.
- `min_time_left` _int_ - The minimum time left before the agent's registration expires
  

**Returns**:

- `bool` - True if the agent's registration needs to be updated or will expire sooner
  than the specified minimum time, False otherwise.



#### query_agent_record[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L320)
```python
def query_agent_record(
        address: str) -> tuple[int, list[AgentEndpoint], list[str]]
```

Get the records associated with an agent's registration.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

  tuple[int, list[AgentEndpoint], list[str]]: The expiry height of the agent's
  registration, the agent's endpoints, and the agent's protocols.



#### get_expiry[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L357)
```python
def get_expiry(address: str) -> int
```

Get the approximate seconds to expiry of an agent's registration.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `int` - The approximate seconds to expiry of the agent's registration.



#### get_endpoints[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L369)
```python
def get_endpoints(address: str) -> list[AgentEndpoint]
```

Get the endpoints associated with an agent's registration.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `list[AgentEndpoint]` - The agent's registered endpoints.



#### get_protocols[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L381)
```python
def get_protocols(address: str) -> list[str]
```

Get the protocols associated with an agent's registration.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `list[str]` - The agent's registered protocols.



#### register[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L415)
```python
async def register(ledger: LedgerClient,
                   wallet: LocalWallet,
                   agent_address: str,
                   protocols: list[str],
                   endpoints: list[AgentEndpoint],
                   signature: str,
                   current_time: int,
                   *,
                   broadcast_retries: int | None = None,
                   broadcast_retry_delay: RetryDelayFunc | None = None,
                   poll_retries: int | None = None,
                   poll_retry_delay: RetryDelayFunc | None = None) -> None
```

Register an agent with the Almanac contract.

**Arguments**:

- `ledger` _LedgerClient_ - The Ledger client.
- `wallet` _LocalWallet_ - The agent's wallet.
- `agent_address` _str_ - The agent's address.
- `protocols` _list[str]_ - List of protocols.
- `endpoints` _list[dict[str, Any]]_ - List of endpoint dictionaries.
- `signature` _str_ - The agent's signature.



#### register_batch[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L494)
```python
async def register_batch(
        ledger: LedgerClient,
        wallet: LocalWallet,
        agent_records: list[AlmanacContractRecord],
        *,
        broadcast_retries: int | None = None,
        broadcast_retry_delay: RetryDelayFunc | None = None,
        poll_retries: int | None = None,
        poll_retry_delay: RetryDelayFunc | None = None) -> None
```

Register multiple agents with the Almanac contract.

**Arguments**:

- `ledger` _LedgerClient_ - The Ledger client.
- `wallet` _LocalWallet_ - The wallet of the registration sender.
- `agents` _list[ALmanacContractRecord]_ - The list of signed agent records to register.



#### get_sequence[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L573)
```python
def get_sequence(address: str) -> int
```

Get the agent's sequence number for Almanac registration.

**Arguments**:

- `address` _str_ - The agent's address.
  

**Returns**:

- `int` - The agent's sequence number.



#### get_almanac_contract[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L597)
```python
def get_almanac_contract(
        network: AgentNetwork = "testnet") -> AlmanacContract | None
```

Get the AlmanacContract instance.

**Arguments**:

- `network` _AgentNetwork_ - The network to use. Defaults to "testnet".
  

**Returns**:

  AlmanacContract | None: The AlmanacContract instance if version is supported.



## NameServiceContract Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L614)

```python
class NameServiceContract(LedgerContract)
```

A class representing the NameService contract for managing domain names and ownership.

This class provides methods to interact with the NameService contract, including
checking name availability, checking ownership, querying domain public status,
obtaining registration transaction details, and registering a name within a domain.



#### query_contract[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L623)
```python
def query_contract(query_msg: dict[str, Any]) -> Any
```

Execute a query with additional checks and error handling.

**Arguments**:

- `query_msg` _dict[str, Any]_ - The query message.
  

**Returns**:

- `Any` - The query response.
  

**Raises**:

- `ValueError` - If the response from contract is not a dict.



#### is_name_available[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L652)
```python
def is_name_available(name: str, domain: str) -> bool
```

Check if a name is available within a domain.

**Arguments**:

- `name` _str_ - The name to check.
- `domain` _str_ - The domain to check within.
  

**Returns**:

- `bool` - True if the name is available, False otherwise.



#### is_owner[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L666)
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



#### is_domain_public[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L687)
```python
def is_domain_public(domain: str) -> bool
```

Check if a domain is public.

**Arguments**:

- `domain` _str_ - The domain to check.
  

**Returns**:

- `bool` - True if the domain is public, False otherwise.



#### get_previous_records[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L704)
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



#### get_registration_tx[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L722)
```python
def get_registration_tx(name: str, wallet_address: Address,
                        agent_records: list[dict[str, Any]] | str, domain: str,
                        duration: int, network: AgentNetwork,
                        approval_token: str) -> Transaction | None
```

Get the registration transaction for registering a name within a domain.

**Arguments**:

- `name` _str_ - The name to be registered.
- `wallet_address` _str_ - The wallet address initiating the registration.
- `agent_address` _str_ - The address of the agent.
- `domain` _str_ - The domain in which the name is registered.
- `duration` _int_ - The duration in seconds for which the name is to be registered.
- `network` _AgentNetwork_ - The network in which the transaction is executed.
- `approval_token` _str_ - The approval token required for registration.
  

**Returns**:

  Transaction | None: The registration transaction, or None if the name is not
  available or not owned by the wallet address.



#### register[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L798)
```python
async def register(ledger: LedgerClient,
                   wallet: LocalWallet,
                   agent_records: str | list[str] | dict[str, dict] | None,
                   name: str,
                   domain: str,
                   approval_token: str,
                   duration: int = ANAME_REGISTRATION_SECONDS,
                   overwrite: bool = True) -> None
```

Register a name within a domain using the NameService contract.

**Arguments**:

- `ledger` _LedgerClient_ - The Ledger client.
- `wallet` _LocalWallet_ - The wallet of the agent.
- `agent_records` _str | list[str] | dict[str, dict] | None_ - The agent records
  to be registered.
- `name` _str_ - The name to be registered.
- `domain` _str_ - The domain in which the name is registered.
- `duration` _int_ - The duration in seconds for which the name is to be registered.
- `approval_token` _str_ - The approval token required for registration.
- `overwrite` _bool, optional_ - Specifies whether to overwrite any existing
  addresses registered to the domain. If False, the address will be
  appended to the previous records. Defaults to True.



#### unregister[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L887)
```python
async def unregister(name: str, domain: str, wallet: LocalWallet) -> None
```

Unregister a name within a domain using the NameService contract.

**Arguments**:

- `name` _str_ - The name to be unregistered.
- `domain` _str_ - The domain in which the name is registered.
- `wallet` _LocalWallet_ - The wallet of the agent.



#### get_name_service_contract[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/network.py#L925)
```python
def get_name_service_contract(
        network: AgentNetwork = "testnet") -> NameServiceContract
```

Get the NameServiceContract instance.

**Arguments**:

- `network` _AgentNetwork, optional_ - The network to use. Defaults to "testnet".
  

**Returns**:

- `NameServiceContract` - The NameServiceContract instance.

