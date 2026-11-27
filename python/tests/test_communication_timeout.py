import asyncio
import time
import unittest

from aiohttp import web
from uagents_core.envelope import Envelope  # noqa: F401 (envelope payload typing)
from uagents_core.identity import Identity
from uagents_core.types import DeliveryStatus, MsgStatus

from uagents import Model
from uagents.communication import send_message, send_sync_message


class Msg(Model):
    text: str


class Resp(Model):
    text: str


class SlowServer:
    """Local HTTP endpoint that answers envelopes after a configurable delay."""

    def __init__(self, delay: float):
        self.delay = delay
        self.endpoint = ""
        self._runner: web.AppRunner | None = None

    async def __aenter__(self) -> "SlowServer":
        app = web.Application()
        app.router.add_post("/submit", self._handle)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "127.0.0.1", 0)
        await site.start()
        port = self._runner.addresses[0][1]
        self.endpoint = f"http://127.0.0.1:{port}/submit"
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._runner:
            await self._runner.cleanup()

    async def _handle(self, request: web.Request) -> web.Response:
        env = await request.json()
        await asyncio.sleep(self.delay)
        return web.json_response(
            {
                "version": 1,
                "sender": env["target"],
                "target": env["sender"],
                "session": env["session"],
                "schema_digest": env["schema_digest"],
                "protocol": env.get("protocol"),
                "payload": env["payload"],
                "expires": env["expires"],
            }
        )


class DirectResolver:
    """Resolves every destination to a single fixed endpoint."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    async def resolve(self, destination: str):
        return destination, [self.endpoint]


class TestSendMessageTimeout(unittest.IsolatedAsyncioTestCase):
    async def test_send_sync_message_times_out_http_request(self):
        async with SlowServer(delay=3.0) as server:
            start = time.perf_counter()
            result = await send_sync_message(
                "agent1qfakeaddress",
                Msg(text="hello"),
                response_type=Resp,
                timeout=1,
                sender=Identity.generate(),
                resolver=DirectResolver(server.endpoint),
            )
            elapsed = time.perf_counter() - start

        self.assertLess(elapsed, 2.5)
        self.assertIsInstance(result, MsgStatus)
        self.assertEqual(result.status, DeliveryStatus.FAILED)

    async def test_send_message_times_out_http_request(self):
        async with SlowServer(delay=3.0) as server:
            start = time.perf_counter()
            result = await send_message(
                "agent1qfakeaddress",
                Msg(text="hello"),
                timeout=1,
                sender=Identity.generate(),
                resolver=DirectResolver(server.endpoint),
            )
            elapsed = time.perf_counter() - start

        self.assertLess(elapsed, 2.5)
        self.assertEqual(result.status, DeliveryStatus.FAILED)

    async def test_send_sync_message_success_within_timeout(self):
        async with SlowServer(delay=0.0) as server:
            result = await send_sync_message(
                "agent1qfakeaddress",
                Msg(text="hello"),
                response_type=Resp,
                timeout=5,
                sender=Identity.generate(),
                resolver=DirectResolver(server.endpoint),
            )

        self.assertIsInstance(result, Resp)
        self.assertEqual(result.text, "hello")


if __name__ == "__main__":
    unittest.main()
