# uAgents-Core

Core definitions and functionalities for building agents that interact with the Fetch.ai ecosystem and Agentverse marketplace.

## Installation

```bash
pip install uagents-core
```

## Quick Start

### Register a Chat Agent with Agentverse

```python
from uagents_core.utils.registration import (
    AgentverseRequestError,
    RegistrationRequestCredentials,
    register_chat_agent,
)

credentials = RegistrationRequestCredentials(
    agent_seed_phrase="my-agent-seed-phrase",
    agentverse_api_key="your-agentverse-api-key",
)

try:
    register_chat_agent(
        name="My Agent",
        endpoint="https://your-agent-endpoint.com/webhook",
        active=True,
        credentials=credentials,
        readme="# My Agent\nHandles customer questions.",
        metadata={
            "categories": ["support"],
            "is_public": "True",
        },
    )
    print("Agent registered successfully!")
except AgentverseRequestError as error:
    print(f"Registration failed: {error}")
    # Access the underlying HTTP/network exception:
    print(f"Caused by: {error.from_exc}")
```

## Key Features

### Permanent Registration

Registrations via the v2 API are **permanent** - no need for periodic refresh:

- Agentverse handles Almanac synchronization automatically
- No 48-hour expiration like v1
- Register once when agent is created

### Agent Identity

Create and manage agent identities:

```python
from uagents_core.identity import Identity

# Create from seed (deterministic)
identity = Identity.from_seed("my-seed-phrase", 0)

# Get agent address
print(identity.address)  # agent1q...

# Sign messages
signature = identity.sign(b"message")
```

### Configuration

```python
from uagents_core.config import AgentverseConfig

config = AgentverseConfig()
print(config.agents_api)    # https://agentverse.ai/v2/agents
print(config.identity_api)  # https://agentverse.ai/v2/identity
print(config.almanac_api)   # https://agentverse.ai/v1/almanac
```

## Available Functions

### Registration

| Function | Error Behavior | Purpose |
|----------|---------------|---------|
| `register_chat_agent()` | **Raises** `AgentverseRequestError` | Register a chat agent (recommended) |
| `register_agent()` | **Raises** `AgentverseRequestError` | Register with custom protocols |
| `register_in_agentverse()` | Returns `False` on failure | Low-level registration (error-safe) |
| `update_agent_status()` | Returns `False` on failure | Update agent active/inactive status |
| `register_batch_in_agentverse()` | Returns `False` on failure | Batch registration (deprecated) |

> **Important:** `register_chat_agent()` and `register_agent()` raise `AgentverseRequestError` on failure. Always wrap calls in a try/except block to handle network errors, authentication failures, and server errors gracefully.

### Error Handling

All HTTP and network errors are wrapped in `AgentverseRequestError`, which provides:

- A human-readable error message (e.g., `"HTTP error: 401 Unauthorized"`)
- The original exception via the `from_exc` attribute for inspection

```python
from uagents_core.utils.registration import AgentverseRequestError

try:
    register_chat_agent(...)
except AgentverseRequestError as error:
    print(f"What went wrong: {error}")
    print(f"Original exception: {error.from_exc}")

    # Common failure patterns:
    # - "Connection error ..."     → Network/DNS issue
    # - "Operation timed out."     → Request exceeded 10s timeout
    # - "HTTP error: 401 ..."      → Invalid or expired API key
    # - "HTTP error: 409 ..."      → Agent address already claimed
    # - "Unexpected server error." → HTTP 500, retry after delay
```

### Models

| Model | Purpose |
|-------|---------|
| `RegistrationRequestCredentials` | API key and agent seed phrase |
| `AgentverseRegistrationRequest` | Full agent registration data |
| `AgentverseRequestError` | Registration failure exception |
| `RegistrationRequest` | Agent registration data (internal) |
| `AgentProfile` | Agent profile (description, readme, avatar) |
| `AgentverseConnectRequest` | Connection credentials (internal) |
| `Identity` | Agent identity and signing |

## Upgrading

See [UPGRADING.md](../docs/UPGRADING.md) for migration guides between versions.

## Related Packages

- **[uagents](https://pypi.org/project/uagents/)** - Full agent framework with decorators and runtime
- **[uagents-adapter](../uagents-adapter/)** - Adapters for LangChain, CrewAI, MCP

## License

Apache 2.0 - See [LICENSE](../../LICENSE) for details.
