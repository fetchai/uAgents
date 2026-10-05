"""
Reusable async HTTP transport with retry and exponential backoff.

``RetryTransport`` wraps an ``httpx.AsyncClient`` and retries transient
failures (network errors, 5xx, 401) with exponential backoff and full
jitter.  Permanent client errors (4xx except 401) are raised immediately
so callers can handle them without waiting through pointless retries.
"""

import asyncio
import logging
import random

import httpx


def _is_permanent_client_error(
    error: httpx.HTTPStatusError,
) -> bool:
    """Return True for 4xx errors that will not resolve on retry.

    401 is excluded because attestation tokens are short-lived
    and a fresh token on the next attempt may succeed.
    """
    code = error.response.status_code
    return 400 <= code < 500 and code != 401


class RetryTransport:
    """Async HTTP POST with exponential backoff and full jitter.

    If an ``httpx.AsyncClient`` is provided, it is reused as-is.
    Otherwise a temporary client is created and closed per call.

    ``max_attempts`` counts only retries, not the initial request.
    ``max_attempts=3`` means 1 initial try + up to 3 retries = 4
    total attempts.  Set to ``None`` for unlimited retries (useful
    for long-lived background workers like event dispatchers).
    """

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        timeout_s: float = 10.0,
        max_attempts: int | None = 5,
        base_delay_s: float = 1.0,
        max_delay_s: float = 30.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self._client = client
        self._timeout_s = timeout_s
        self._max_attempts = max_attempts
        self._base_delay_s = base_delay_s
        self._max_delay_s = max_delay_s
        self._logger = logger

    async def post(
        self,
        url: str,
        content: str | bytes,
        headers: dict[str, str],
    ) -> httpx.Response:
        """POST with retry.

        Raises ``httpx.HTTPStatusError`` on permanent 4xx.
        Raises the last exception if max attempts are exhausted.
        """
        return await self._request(
            "POST", url, content=content, headers=headers
        )

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Execute an HTTP request with retry and backoff."""
        client = self._client or httpx.AsyncClient(
            timeout=self._timeout_s
        )
        attempts = 0
        last_exc: Exception | None = None
        try:
            while True:
                try:
                    response = await client.request(
                        method, url, **kwargs
                    )
                    response.raise_for_status()
                    return response
                except httpx.HTTPStatusError as exc:
                    if _is_permanent_client_error(exc):
                        raise
                    last_exc = exc
                    if self._logger is not None:
                        self._logger.error(
                            "HTTP %s failed (%d): %s",
                            method,
                            exc.response.status_code,
                            exc,
                        )
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if self._logger is not None:
                        self._logger.error(
                            "HTTP %s failed: %s",
                            method,
                            exc,
                        )
                if (
                    self._max_attempts is not None
                    and attempts >= self._max_attempts
                ):
                    raise last_exc  # type: ignore[misc]
                cap = min(
                    self._base_delay_s * (2**attempts),
                    self._max_delay_s,
                )
                delay = random.uniform(0, cap)
                attempts += 1
                await asyncio.sleep(delay)
        finally:
            if client is not self._client:
                await client.aclose()
