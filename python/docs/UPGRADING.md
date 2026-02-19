# Upgrading uAgents / uagents-core

This guide helps you migrate between major versions of uAgents and uagents-core.

## Table of Contents

- [Error Propagation Fix (0.4.1)](#error-propagation-fix-041)
- [From uagents-core 0.3.x to 0.4.0](#from-uagents-core-03x-to-040)
- [Version Compatibility Matrix](#version-compatibility-matrix)

---

## Error Propagation Fix (0.4.1)

### What Changed

`register_agent()` and `register_chat_agent()` now **raise `AgentverseRequestError`** when registration fails, instead of silently swallowing the error and returning `None`.

This is a **behavioral fix** -- the previous behavior was a bug where registration failures were logged but not communicated to callers, making it impossible to detect failed registrations.

### Who Is Affected

If you call `register_agent()` or `register_chat_agent()` **without** a try/except block, your code will now raise an unhandled exception when registration fails (network error, bad credentials, server error, etc.).

### How to Update

Wrap calls in a try/except block:

```python
from uagents_core.utils.registration import (
    AgentverseRequestError,
    RegistrationRequestCredentials,
    register_chat_agent,
)

credentials = RegistrationRequestCredentials(
    agent_seed_phrase="my-seed",
    agentverse_api_key="my-key",
)

try:
    register_chat_agent(
        name="My Agent",
        endpoint="https://example.com/webhook",
        active=True,
        credentials=credentials,
    )
    print("Registration succeeded")
except AgentverseRequestError as error:
    print(f"Registration failed: {error}")
    # Optionally inspect the underlying exception:
    print(f"Caused by: {error.from_exc}")
```

### Functions That Raise vs Return

| Function | On failure... | Notes |
|----------|---------------|-------|
| `register_chat_agent()` | **Raises** `AgentverseRequestError` | Recommended for chat agents |
| `register_agent()` | **Raises** `AgentverseRequestError` | Recommended for custom protocols |
| `register_in_agentverse()` | Returns `False` | Error-safe wrapper, logs internally |
| `update_agent_status()` | Returns `False` | Error-safe wrapper, logs internally |
| `register_batch_in_agentverse()` | Returns `False` | Deprecated |

If you prefer boolean return values without exception handling, use `register_in_agentverse()` or `update_agent_status()` instead.

---

## From uagents-core 0.3.x to 0.4.0

### Overview

Version 0.4.0 introduces a **simplified registration model** with significant architectural changes:

| Aspect | 0.3.x | 0.4.0 |
|--------|-------|-------|
| Almanac API registration expiration | 7 days | **Permanent** (linked to user account expiry) |
| Almanac registration | Separate API call required | **Automatic** (handled by Agentverse) |
| Periodic refresh | Required every ~7 days | **Not needed** |
| Batch registration | Supported | **Deprecated** |

### Key Benefits

1. **Register once** - No need for periodic refresh tasks
2. **Simpler architecture** - Agentverse handles Almanac synchronization
3. **Reduced complexity** - Remove expiration tracking and refresh infrastructure

---

### Breaking Changes

#### Registration API Changes

| 0.3.x | 0.4.0 | Notes |
|-------|-------|-------|
| `AgentRegistrationInput` | `RegistrationRequest` | New model with different fields |
| `register_batch_in_almanac()` | **Deprecated** | Use `register_chat_agent()` or `register_in_agentverse()` individually |
| N/A | `register_in_agentverse()` | New primary registration function |
| N/A | DELETE `/v2/agents/{address}` | New agent removal capability |

#### New Required Fields

The `RegistrationRequest` model requires fields that were optional in `AgentRegistrationInput`:

```python
from uagents_core.registration import RegistrationRequest, AgentProfile

# 0.4.0 requires these fields:
request = RegistrationRequest(
    address="agent1q...",           # Required: bech32 agent address
    name="My Agent",                # Required: 1-80 characters
    agent_type="uagent",             # Optional: defaults to "uagent"
    profile=AgentProfile(           # Optional: agent profile
        description="Short desc",   # Max 300 chars
        readme="Detailed readme",   # Max 80000 chars
        avatar_url="https://...",   # Max 4000 chars
    ),
    endpoints=[...],                # Optional: list of AgentEndpoint
    protocols=[...],                # Optional: list of protocol digests
    metadata={...},                 # Optional: additional metadata
)
```

#### Handle Uniqueness

The `handle` field in `RegistrationRequest` is now **globally unique**. Choose handles carefully as they cannot be reused across the platform.

---

### Migration Guide

#### Step 1: Update Dependencies

```bash
pip install uagents-core>=0.4.0
```

Or in your requirements file:

```
uagents-core>=0.4.0,<0.5.0
```

#### Step 2: Update Registration Code

**Before (0.3.x) - Batch registration with periodic refresh:**

```python
from uagents_core.utils.registration import (
    AgentRegistrationInput,
    register_batch_in_almanac,
)

# This was called every ~2 hours to refresh before 48hr expiration
def refresh_registrations():
    items = [
        AgentRegistrationInput(
            identity=identity,
            endpoints=[endpoint],
            protocol_digests=[protocol_digest],
            metadata={"key": "value"},
        )
        for agent in agents_to_refresh
    ]
    
    success, failed = register_batch_in_almanac(items, agentverse_config=config)
```

**After (0.4.0) - Individual registration, once per agent:**

```python
from uagents_core.utils.registration import (
    register_in_agentverse,
    AgentverseRegistrationRequest,
)
from uagents_core.registration import AgentverseConnectRequest
from uagents_core.identity import Identity
from uagents_core.config import AgentverseConfig

def register_agent(agent_seed: str, name: str, endpoint: str, api_key: str) -> bool:
    """
    Register an agent to Agentverse. Call once on agent creation.
    Registration is permanent - no refresh needed.
    """
    identity = Identity.from_seed(agent_seed, 0)
    
    connect_request = AgentverseConnectRequest(
        user_token=api_key,
        agent_type="proxy",
        endpoint=endpoint,
    )
    
    agent_details = AgentverseRegistrationRequest(
        name=name,
        endpoint=endpoint,
        protocols=[your_protocol_digest],
        description="Agent description",
        readme="Detailed agent readme",
    )
    
    return register_in_agentverse(
        request=connect_request,
        identity=identity,
        agent_details=agent_details,
        agentverse_config=AgentverseConfig(),
    )
```

#### Step 3: Remove Refresh Infrastructure

Since registrations are now permanent, you can remove:

- **Periodic refresh tasks** (Celery, cron jobs, etc.)
- **Expiration tracking** (e.g., `last_registered_at` timestamps)
- **Refresh interval settings**
- **Batch registration code**

#### Step 4: Update Agent Removal (Optional)

If you need to remove agents from Agentverse, use the new DELETE endpoint:

```python
import requests

def delete_agent(agent_address: str, api_key: str) -> bool:
    """Remove an agent from Agentverse."""
    response = requests.delete(
        f"https://agentverse.ai/v2/agents/{agent_address}",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    return response.status_code == 200
```

---

### Batch Registration Deprecation

**Batch registration is deprecated in 0.4.0.** Since registrations no longer expire, there's no need to refresh multiple agents simultaneously.

For large imports or backfills:

```python
import time

def backfill_agents(agents: list, api_key: str):
    """Register multiple agents with rate limiting."""
    for agent in agents:
        success = register_agent(
            agent_seed=agent.seed,
            name=agent.name,
            endpoint=agent.endpoint,
            api_key=api_key,
        )
        if success:
            print(f"Registered: {agent.name}")
        else:
            print(f"Failed: {agent.name}")
        
        # Rate limit: wait between requests
        time.sleep(0.1)
```

---

### API Endpoints Reference

| Purpose | v1 (deprecated) | v2 (current) |
|---------|-----------------|--------------|
| Agent registration | `/v1/almanac` | `/v2/agents` |
| Identity proof | N/A | `/v2/identity` |
| Agent removal | N/A | DELETE `/v2/agents/{address}` |

The v2 API automatically syncs registrations to Almanac. You no longer need to call `/v1/almanac` directly.

---

### FAQ

**Q: Do I still need to refresh registrations periodically?**

No. V2 registrations are permanent. Agentverse handles Almanac synchronization automatically.

**Q: What happens to my existing agents registered via v1?**

They will continue to work. However, you should migrate to v2 and remove your refresh infrastructure.

**Q: Can I still use batch registration?**

The function exists for backwards compatibility, but it's deprecated. Use individual `register_chat_agent()` or `register_agent()` calls instead.

**Q: How do I update an agent's profile after registration?**

Call `register_chat_agent()` or `register_agent()` again with the updated details. It will update the existing registration.

**Q: How do I handle registration errors?**

Wrap `register_chat_agent()` or `register_agent()` in a try/except for `AgentverseRequestError`. See the [Error Propagation Fix](#error-propagation-fix-041) section for examples.

**Q: How do I remove an agent from Agentverse?**

Use the DELETE endpoint: `DELETE /v2/agents/{agent_address}`

---

## Version Compatibility Matrix

| uagents | uagents-core | Python | Notes |
|---------|--------------|--------|-------|
| 0.23.x | >=0.4.0 | 3.10-3.13 | Current version |
| 0.22.x | 0.3.x | 3.10-3.12 | Requires periodic refresh |
| 0.21.x | 0.3.x | 3.10-3.12 | Requires periodic refresh |

---

## Getting Help

- [GitHub Issues](https://github.com/fetchai/uAgents/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/fetchai/uAgents/discussions) - Questions and general discussion
- [Official Documentation](https://uagents.fetch.ai/docs) - Full documentation
