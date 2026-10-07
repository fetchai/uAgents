import asyncio
import inspect
from collections.abc import Awaitable, Callable
from enum import Enum

from uagents_core.protocol import ProtocolSpecification

from uagents import Context, Model, Protocol


class HealthCheck(Model):
    pass


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class AgentHealth(Model):
    agent_name: str
    status: HealthStatus


health_protocol_spec = ProtocolSpecification(
    name="HealthProtocol",
    version="0.1.0",
    interactions={
        HealthCheck: {AgentHealth},
        AgentHealth: set(),
    },
    roles={
        "agent": {HealthCheck},
        "monitor": {AgentHealth},
    },
)

HealthCheckCallback = Callable[[Context], bool | Awaitable[bool]]


async def _run_check(check: HealthCheckCallback, ctx: Context) -> bool:
    if inspect.iscoroutinefunction(check):
        return bool(await check(ctx))

    result = await asyncio.to_thread(check, ctx)
    if inspect.isawaitable(result):
        result = await result
    return bool(result)


class HealthProtocol(Protocol):
    """Standard health protocol backed by an application-defined health check."""

    def __init__(
        self,
        *,
        agent_name: str,
        check: HealthCheckCallback,
    ):
        super().__init__(spec=health_protocol_spec, role="agent")

        @self.on_message(HealthCheck)
        async def _health_check_handler(
            ctx: Context, sender: str, _msg: HealthCheck
        ) -> None:
            status = HealthStatus.UNHEALTHY
            try:
                if await _run_check(check, ctx):
                    status = HealthStatus.HEALTHY
            except Exception as error:
                ctx.logger.error(f"Health check failed: {error}")
            finally:
                await ctx.send(
                    sender,
                    AgentHealth(agent_name=agent_name, status=status),
                )
