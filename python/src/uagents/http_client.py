"""HTTP client utilities for uAgents using aiohttp."""

import logging
from contextlib import asynccontextmanager
from typing import Any

import aiohttp

LOGGER = logging.getLogger("http_client")


class HttpClient:
    """A singleton HTTP client for making async HTTP requests."""

    _instance = None
    _session: aiohttp.ClientSession | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    @asynccontextmanager
    async def get_session(cls):
        """Get or create an aiohttp ClientSession."""
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession()
        try:
            yield cls._session
        except Exception as e:
            LOGGER.error(f"Error in HTTP session: {e}")
            raise

    @classmethod
    async def close(cls):
        """Close the HTTP session if it exists."""
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None

    @classmethod
    async def get(
        cls, url: str, params: dict[str, Any] | None = None, timeout: int = 5
    ) -> tuple[int, dict[str, Any]]:
        """
        Make an async GET request.

        Args:
            url: The URL to make the request to
            params: Optional query parameters
            timeout: Request timeout in seconds

        Returns:
            Tuple of (status_code, response_json)
        """
        async with cls.get_session() as session:
            try:
                async with session.get(url, params=params, timeout=timeout) as response:
                    return response.status, await response.json()
            except aiohttp.ClientError as e:
                LOGGER.error(f"HTTP request failed: {e}")
                raise


# Global HTTP client instance
http_client = HttpClient()
