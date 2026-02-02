# uAgents-Core

Core definitions and functionalities for building agents that interact with the Fetch.ai ecosystem and Agentverse marketplace.

## Installation

```bash
pip install uagents-core
```

## Quick Start

### Register an Agent with Agentverse

```python
from uagents_core.utils.registration import (
    register_in_agentverse,
    AgentverseRegistrationRequest,
)
from uagents_core.registration import AgentverseConnectRequest
from uagents_core.identity import Identity
from uagents_core.config import AgentverseConfig

# Create agent identity from a seed phrase
identity = Identity.from_seed("my-agent-seed-phrase", 0)

# Prepare registration request
connect_request = AgentverseConnectRequest(
    user_token="your-agentverse-api-key",
    agent_type="proxy",
    endpoint="https://your-agent-endpoint.com",
)

agent_details = AgentverseRegistrationRequest(
    name="My Agent",
    endpoint="https://your-agent-endpoint.com",
    protocols=["your-protocol-digest"],
    description="A helpful agent",
    readme="Detailed description of what this agent does.",
)

# Register the agent (permanent, no refresh needed)
success = register_in_agentverse(
    request=connect_request,
    identity=identity,
    agent_details=agent_details,
    agentverse_config=AgentverseConfig(),
)
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

| Function | Purpose |
|----------|---------|
| `register_in_agentverse()` | Register a single agent (recommended) |
| `register_agent()` | Register with credentials object |
| `register_chat_agent()` | Register agent with chat protocol |
| `update_agent_status()` | Update agent active/inactive status |

### Models

| Model | Purpose |
|-------|---------|
| `RegistrationRequest` | Agent registration data |
| `AgentProfile` | Agent profile (description, readme, avatar) |
| `AgentverseConnectRequest` | Connection credentials |
| `Identity` | Agent identity and signing |

## Upgrading

See [UPGRADING.md](../docs/UPGRADING.md) for migration guides between versions.

## Related Packages

- **[uagents](https://pypi.org/project/uagents/)** - Full agent framework with decorators and runtime
- **[uagents-adapter](../uagents-adapter/)** - Adapters for LangChain, CrewAI, MCP

## License

Apache 2.0 - See [LICENSE](../../LICENSE) for details.
