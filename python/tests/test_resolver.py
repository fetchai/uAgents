import asyncio
import unittest

import aiohttp
from aioresponses import aioresponses

from uagents.resolver import AlmanacApiResolver, almanac_api_get

# We use a mocked Almanac API URI to avoid real network calls.
MOCKED_ALMANAC_API = "http://127.0.0.1:8888/v1/almanac"

TEST_ADDRESS = "agent1qvc0v9ty4lykdd2j8w97emrmmn2ts8kycx9cvr2gz36ssc9ll8ghqgltkky"

TEST_AGENT_RESPONSE = {
    "expiry": "2027-01-01T00:00:00Z",
    "endpoints": [{"url": "https://foobar.com", "weight": 1}],
}


class TestAlmanacApiGet(unittest.IsolatedAsyncioTestCase):
    async def test_returns_status_and_body_on_success(self):
        async with aiohttp.ClientSession() as session:
            with aioresponses() as mocked:
                mocked.get(
                    f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
                    payload={},
                )

                status, body = await almanac_api_get(
                    session,
                    f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
                )

        self.assertEqual(status, 200)
        self.assertEqual(body, {})

    async def test_retries_transient_timeout_then_succeeds(self):
        async with aiohttp.ClientSession() as session:
            with aioresponses() as mocked:
                mocked.get(
                    f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
                    exception=asyncio.TimeoutError(),
                )
                mocked.get(
                    f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
                    payload=TEST_AGENT_RESPONSE,
                )

                status, body = await almanac_api_get(
                    session,
                    f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
                    retry_delay=lambda attempt: 0,  # keep the test fast
                )

        self.assertEqual(status, 200)
        self.assertEqual(body, TEST_AGENT_RESPONSE)

    async def test_does_not_retry_non_200_responses(self):
        # A 404 means the agent is not registered - it is a correct answer,
        # not a transient failure.
        async with aiohttp.ClientSession() as session:
            with aioresponses() as mocked:
                mocked.get(
                    f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
                    status=404,
                )

                status, body = await almanac_api_get(
                    session,
                    f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
                )

        self.assertEqual(status, 404)
        self.assertIsNone(body)

    async def test_raises_after_attempts_exhausted(self):
        async with aiohttp.ClientSession() as session:
            with aioresponses() as mocked:
                for _ in range(2):
                    mocked.get(
                        f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
                        exception=asyncio.TimeoutError(),
                    )

                with self.assertRaises(asyncio.TimeoutError):
                    await almanac_api_get(
                        session,
                        f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
                        retry_delay=lambda attempt: 0,
                    )


class TestAlmanacApiResolverApiResolve(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.resolver = AlmanacApiResolver(almanac_api_url=MOCKED_ALMANAC_API)

    @aioresponses()
    async def test_resolves_endpoints(self, mocked_responses):
        mocked_responses.get(
            f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
            payload=TEST_AGENT_RESPONSE,
        )

        address, endpoints = await self.resolver._api_resolve(TEST_ADDRESS)

        self.assertEqual(address, TEST_ADDRESS)
        self.assertEqual(endpoints, ["https://foobar.com"])

    @aioresponses()
    async def test_recovers_from_transient_timeout(self, mocked_responses):
        mocked_responses.get(
            f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
            exception=asyncio.TimeoutError(),
        )
        mocked_responses.get(
            f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
            payload=TEST_AGENT_RESPONSE,
        )

        # Patch the backoff so the retry is immediate in the test.
        import uagents.resolver as resolver_module

        original_backoff = resolver_module.default_exp_backoff
        resolver_module.default_exp_backoff = lambda attempt: 0
        try:
            address, endpoints = await self.resolver._api_resolve(TEST_ADDRESS)
        finally:
            resolver_module.default_exp_backoff = original_backoff

        self.assertEqual(address, TEST_ADDRESS)
        self.assertEqual(endpoints, ["https://foobar.com"])

    @aioresponses()
    async def test_returns_empty_when_agent_not_registered(self, mocked_responses):
        mocked_responses.get(
            f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
            status=404,
        )

        address, endpoints = await self.resolver._api_resolve(TEST_ADDRESS)

        self.assertIsNone(address)
        self.assertEqual(endpoints, [])

    @aioresponses()
    async def test_returns_empty_after_persistent_timeout(self, mocked_responses):
        for _ in range(2):
            mocked_responses.get(
                f"{MOCKED_ALMANAC_API}/agents/{TEST_ADDRESS}",
                exception=asyncio.TimeoutError(),
            )

        import uagents.resolver as resolver_module

        original_backoff = resolver_module.default_exp_backoff
        resolver_module.default_exp_backoff = lambda attempt: 0
        try:
            address, endpoints = await self.resolver._api_resolve(TEST_ADDRESS)
        finally:
            resolver_module.default_exp_backoff = original_backoff

        self.assertIsNone(address)
        self.assertEqual(endpoints, [])
