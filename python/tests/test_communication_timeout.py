import asyncio
import time
import unittest

from aiohttp import web
from uagents_core.envelope import Envelope  # noqa: F401 (envelope payload typing)
from uagents_core.identity import Identity
from uagents_core.types import DeliveryStatus, MsgStatus

from uagents import Agent, Model
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
    async def asyncSetUp(self):
        self._dispenser_tasks: list[asyncio.Task] = []

    async def _start_dispenser(self, agent: Agent) -> None:
        """Run the agent's dispenser so queued envelopes are actually sent."""
        self._dispenser_tasks.append(asyncio.create_task(agent._dispenser.run()))

    async def asyncTearDown(self):
        for task in self._dispenser_tasks:
            task.cancel()

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


class TestDispenserTimeout(unittest.IsolatedAsyncioTestCase):
    """The dispenser must abort slow HTTP requests so they don't block the queue."""

    def setUp(self) -> None:
        self.agent = Agent(name="timeout-test", seed="timeout test seed")
        self._dispenser_task: asyncio.Task | None = None
        return super().setUp()

    async def asyncTearDown(self) -> None:
        if self._dispenser_task:
            self._dispenser_task.cancel()
        return await super().asyncTearDown()

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self._dispenser_task: asyncio.Task | None = None

    async def test_slow_request_does_not_block_queue(self):
        class AnyResolver:
            def __init__(self, slow: str, fast: str):
                self._slow = slow
                self._fast = fast

            async def resolve(self, destination: str):
                endpoint = self._slow if "slow" in destination else self._fast
                return destination, [endpoint]

        fast_hits: list[float] = []

        async def fast_handle(request: web.Request) -> web.Response:
            fast_hits.append(time.perf_counter())
            return web.json_response({"status": "Sent", "detail": ""})

        app = web.Application()
        app.router.add_post("/submit", fast_handle)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        fast_url = f"http://127.0.0.1:{runner.addresses[0][1]}/submit"
        self._dispenser_task = asyncio.create_task(self.agent._dispenser.run())

        try:
            async with SlowServer(delay=3.0) as slow_server:
                ctx = self.agent._build_context()
                ctx._resolver = AnyResolver(slow=slow_server.endpoint, fast=fast_url)
                start = time.perf_counter()

                # send to the slow endpoint with a short timeout; the POST aborts
                # after 1s but the caller gives up at the same deadline anyway
                slow_task = asyncio.create_task(
                    ctx.send("agent1qslowdest", Msg(text="slow"), timeout=1)
                )
                await asyncio.sleep(0.05)

                # this queued envelope must not wait behind the slow request
                fast_result = await ctx.send(
                    "agent1qfastdest", Msg(text="fast"), timeout=10
                )
                fast_done = time.perf_counter() - start
                slow_result = await slow_task
                slow_done = time.perf_counter() - start

                self.assertEqual(slow_result.status, DeliveryStatus.FAILED)
                self.assertLess(slow_done, 2.5)
                self.assertEqual(fast_result.status, DeliveryStatus.DELIVERED)
                self.assertLess(fast_done, 2.5)
                self.assertTrue(fast_hits, "fast endpoint was never reached")
                self.assertLess(fast_hits[0] - start, 2.5)
        finally:
            await runner.cleanup()


if __name__ == "__main__":
    unittest.main()
