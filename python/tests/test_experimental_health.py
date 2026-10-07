import unittest
from unittest.mock import MagicMock

from uagents import Model
from uagents.experimental.health import (
    AgentHealth,
    HealthCheck,
    HealthProtocol,
    HealthStatus,
    cached_check,
)

HEALTH_PROTOCOL_DIGEST = (
    "proto:507abfddc932972a02d92fbdeee7d0767a7bd1033adcc84e6cd82d377fb90007"
)


class FakeStorage:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value


class FakeContext:
    def __init__(self):
        self.storage = FakeStorage()
        self.logger = MagicMock()
        self.sent = []

    async def send(self, destination, message):
        self.sent.append((destination, message))


class TestHealthProtocol(unittest.IsolatedAsyncioTestCase):
    def test_digest_matches_existing_health_protocol(self):
        protocol = HealthProtocol(
            agent_name="test-agent",
            check=lambda _ctx: True,
        )

        self.assertEqual(protocol.digest, HEALTH_PROTOCOL_DIGEST)
        protocol.verify()

    async def test_async_check_sends_healthy_response(self):
        async def check(_ctx):
            return True

        protocol = HealthProtocol(
            agent_name="test-agent",
            check=check,
        )
        ctx = FakeContext()
        handler = protocol.signed_message_handlers[
            Model.build_schema_digest(HealthCheck)
        ]

        await handler(ctx, "sender", HealthCheck())

        self.assertEqual(len(ctx.sent), 1)
        destination, response = ctx.sent[0]
        self.assertEqual(destination, "sender")
        self.assertEqual(
            response,
            AgentHealth(
                agent_name="test-agent",
                status=HealthStatus.HEALTHY,
            ),
        )

    async def test_check_exception_sends_unhealthy_response(self):
        def check(_ctx):
            raise RuntimeError("provider unavailable")

        protocol = HealthProtocol(
            agent_name="test-agent",
            check=check,
        )
        ctx = FakeContext()
        handler = protocol.signed_message_handlers[
            Model.build_schema_digest(HealthCheck)
        ]

        await handler(ctx, "sender", HealthCheck())

        _, response = ctx.sent[0]
        self.assertEqual(response.status, HealthStatus.UNHEALTHY)
        ctx.logger.error.assert_called_once()

    async def test_cached_check_reuses_fresh_result(self):
        ctx = FakeContext()
        calls = 0

        def probe():
            nonlocal calls
            calls += 1
            return True

        self.assertTrue(await cached_check(ctx, probe))
        self.assertTrue(await cached_check(ctx, probe))
        self.assertEqual(calls, 1)

    async def test_cached_check_supports_async_probe(self):
        ctx = FakeContext()

        async def probe():
            return True

        self.assertTrue(await cached_check(ctx, probe))


if __name__ == "__main__":
    unittest.main()
