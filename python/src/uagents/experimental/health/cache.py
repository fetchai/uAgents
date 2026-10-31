import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable

from uagents import Context

DEFAULT_TTL_SECONDS = 24 * 60 * 60
PROBE_TIMEOUT_SECONDS = 5

HealthProbe = Callable[[], bool | Awaitable[bool]]


async def _run_probe(probe: HealthProbe) -> bool:
    if inspect.iscoroutinefunction(probe):
        return bool(await probe())

    result = await asyncio.to_thread(probe)
    if inspect.isawaitable(result):
        result = await result
    return bool(result)


async def cached_check(
    ctx: Context,
    probe: HealthProbe,
    *,
    cache_key: str = "dependency_health",
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    timeout_seconds: int = PROBE_TIMEOUT_SECONDS,
) -> bool:
    """Run a bounded dependency probe when its stored result is stale."""
    now = int(time.time())
    cached = ctx.storage.get(cache_key)
    if isinstance(cached, dict) and now - cached.get("checked_at", 0) < ttl_seconds:
        healthy = bool(cached.get("healthy"))
        ctx.logger.info(
            f"Dependency health check [{cache_key}]: "
            f"{'PASSED' if healthy else 'FAILED'} (cached result)"
        )
        return healthy

    try:
        healthy = await asyncio.wait_for(_run_probe(probe), timeout=timeout_seconds + 1)
    except Exception as error:
        ctx.logger.warning(f"Dependency health check failed: {error}")
        healthy = False

    ctx.storage.set(cache_key, {"checked_at": now, "healthy": healthy})
    ctx.logger.info(
        f"Dependency health check [{cache_key}]: "
        f"{'PASSED' if healthy else 'FAILED'} (live probe)"
    )
    return healthy
