# Experimental Health Protocol

`HealthProtocol` provides a reusable health-check protocol for uAgents. It:

- Responds to `HealthCheck` messages with `AgentHealth`
- Reports `HEALTHY` or `UNHEALTHY`
- Supports synchronous and asynchronous health checks
- Converts check failures into an `UNHEALTHY` response
- Includes an optional cached provider check with a 24-hour default TTL

## Add health checks to an agent

For an agent without an external dependency:

```python
from uagents import Agent
from uagents.experimental.health import HealthProtocol

agent = Agent(name="example", seed="example seed")

health_protocol = HealthProtocol(
    agent_name=agent.name,
    check=lambda _ctx: True,
)

agent.include(health_protocol, publish_manifest=True)
```

For an agent that depends on an external provider:

```python
from uagents import Context
from uagents.experimental.health import HealthProtocol, cached_check


def provider_is_available() -> bool:
    # Make a small provider request and return whether it succeeded.
    ...


async def agent_is_healthy(ctx: Context) -> bool:
    return await cached_check(ctx, provider_is_available)


health_protocol = HealthProtocol(
    agent_name=agent.name,
    check=agent_is_healthy,
)

agent.include(health_protocol, publish_manifest=True)
```

`cached_check` stores the latest result in the agent's storage. By default, it
runs the provider probe at most once every 24 hours and bounds the probe with a
timeout. Use `ttl_seconds`, `timeout_seconds`, and `cache_key` to customize this
behavior.

## Check an agent's health

A monitoring agent can use the shared message models:

```python
from uagents import Agent, Context
from uagents.experimental.health import AgentHealth, HealthCheck

monitor = Agent(name="health-monitor", seed="health monitor seed")


@monitor.on_event("startup")
async def check_agent(ctx: Context):
    await ctx.send("<agent-address>", HealthCheck())


@monitor.on_message(AgentHealth)
async def handle_agent_health(ctx: Context, sender: str, msg: AgentHealth):
    ctx.logger.info(f"{msg.agent_name} ({sender}): {msg.status.value}")
```

The package also exports `HealthStatus` and `health_protocol_spec` for consumers
that need the status enum or protocol specification directly.

This API is experimental and may change before becoming stable.
