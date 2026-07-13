# pylint: disable=protected-access
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from pydantic import ValidationError
from uagents_core.config import AgentverseConfig
from uagents_core.events import (
    DEFAULT_SDK_VERSION,
    AgentBatchEvents,
    BatchEvent,
    MessageEventMetadata,
    PlatformMetadata,
    dispatch_events,
    is_registered_on_agentverse,
)
from uagents_core.identity import Identity

from uagents import Agent
from uagents.context import InternalContext

SDK_VERSION = "9.9.9"


def _mock_async_client(response=None, side_effect=None):
    """Build a replacement for httpx.AsyncClient supporting `async with`."""
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    if side_effect is not None:
        client.get = AsyncMock(side_effect=side_effect)
        client.post = AsyncMock(side_effect=side_effect)
    else:
        client.get = AsyncMock(return_value=response)
        client.post = AsyncMock(return_value=response)
    return MagicMock(return_value=client), client


class TestEventBuilders(unittest.TestCase):
    def test_from_message_defaults(self):
        batch = AgentBatchEvents.from_message("Agent Started", SDK_VERSION)
        self.assertEqual(batch.platform.sdk_version, SDK_VERSION)
        self.assertEqual(len(batch.events), 1)
        event = batch.events[0]
        self.assertEqual(event.category, "user")
        self.assertEqual(event.kind, "info")
        self.assertEqual(event.message, "Agent Started")
        self.assertIsNone(event.metadata)

    def test_default_sdk_version_resolved(self):
        # uagents is installed in the test env, so the default must not be a
        # placeholder and must flow through the builders when not passed.
        self.assertNotEqual(DEFAULT_SDK_VERSION, "unknown")
        self.assertEqual(PlatformMetadata.current().sdk_version, DEFAULT_SDK_VERSION)
        batch = AgentBatchEvents.from_message("Agent Started")
        self.assertEqual(batch.platform.sdk_version, DEFAULT_SDK_VERSION)

    def test_from_exception(self):
        exc = ValueError("boom")
        batch = AgentBatchEvents.from_exception(exc, "traceback-text", SDK_VERSION)
        event = batch.events[0]
        self.assertEqual(event.kind, "error")
        self.assertEqual(event.category, "system")
        self.assertEqual(event.exception, "ValueError")
        self.assertEqual(event.traceback, "traceback-text")
        self.assertEqual(event.message, "boom")

    def test_message_event_metadata_validated(self):
        metadata = MessageEventMetadata(
            direction="received",
            peer="agent1xyz",
            msg_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
        )
        event = BatchEvent(
            category="user",
            kind="message",
            timestamp=datetime.now(timezone.utc),
            metadata=metadata.model_dump(mode="json"),
            message="Message received from agent1xyz",
        )
        self.assertEqual(event.metadata["direction"], "received")

    def test_message_event_metadata_invalid_raises(self):
        with self.assertRaises(ValidationError):
            BatchEvent(
                category="user",
                kind="message",
                timestamp=datetime.now(timezone.utc),
                metadata={"direction": "sideways"},
            )


class TestRegistrationCheck(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = Identity.generate()
        self.agentverse = AgentverseConfig()

    async def test_registered_returns_true_on_200(self):
        factory, _ = _mock_async_client(response=MagicMock(status_code=200))
        with patch("uagents_core.events.httpx.AsyncClient", factory):
            result = await is_registered_on_agentverse(self.identity, self.agentverse)
        self.assertTrue(result)

    async def test_registered_returns_false_on_404(self):
        factory, _ = _mock_async_client(response=MagicMock(status_code=404))
        with patch("uagents_core.events.httpx.AsyncClient", factory):
            result = await is_registered_on_agentverse(self.identity, self.agentverse)
        self.assertFalse(result)

    async def test_registered_returns_false_on_network_error(self):
        factory, _ = _mock_async_client(side_effect=httpx.ConnectError("nope"))
        with patch("uagents_core.events.httpx.AsyncClient", factory):
            result = await is_registered_on_agentverse(self.identity, self.agentverse)
        self.assertFalse(result)


class TestDispatchEvents(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = Identity.generate()
        self.agentverse = AgentverseConfig()
        self.batch = AgentBatchEvents.from_message("Agent Started", SDK_VERSION)

    async def test_dispatch_posts_to_events_endpoint(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        factory, client = _mock_async_client(response=response)
        with patch("uagents_core.events.httpx.AsyncClient", factory):
            await dispatch_events(self.identity, self.agentverse, self.batch)
        client.post.assert_awaited_once()
        url = client.post.await_args.args[0]
        self.assertTrue(url.endswith("/v1/events"))

    async def test_dispatch_swallows_errors(self):
        factory, _ = _mock_async_client(side_effect=httpx.ConnectError("down"))
        with patch("uagents_core.events.httpx.AsyncClient", factory):
            # Must not raise.
            await dispatch_events(self.identity, self.agentverse, self.batch)


class TestGatingMatrix(unittest.IsolatedAsyncioTestCase):
    async def _resolve(self, report_events: bool, registered: bool) -> bool:
        agent = Agent(
            name=f"telemetry-{report_events}-{registered}",
            seed=f"telemetry gating seed {report_events} {registered}",
            enable_agent_inspector=False,
            report_events=report_events,
        )
        with patch(
            "uagents.agent.is_registered_on_agentverse",
            AsyncMock(return_value=registered),
        ):
            await agent._resolve_events_enabled()
        return agent._events_enabled

    async def test_registered_and_toggle_on_enables(self):
        self.assertTrue(await self._resolve(report_events=True, registered=True))

    async def test_registered_but_toggle_off_disables(self):
        self.assertFalse(await self._resolve(report_events=False, registered=True))

    async def test_unregistered_disables_even_when_on(self):
        self.assertFalse(await self._resolve(report_events=True, registered=False))


class TestRuntimeWiring(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = Agent(
            name="telemetry-runtime",
            seed="telemetry runtime seed",
            enable_agent_inspector=False,
        )

    def _fake_context(self):
        context = MagicMock()
        context.session = uuid.uuid4()
        context.validate_replies = MagicMock()
        return context

    async def test_handle_message_reports_received_when_enabled(self):
        self.agent._events_enabled = True
        self.agent._schedule_telemetry = MagicMock()

        async def handler(_ctx, _sender, _msg):
            return None

        await self.agent._handle_message(
            handler, self._fake_context(), "agent1sender", MagicMock(), MagicMock()
        )

        self.assertEqual(self.agent._schedule_telemetry.call_count, 1)
        batch = self.agent._schedule_telemetry.call_args.args[0]
        self.assertEqual(batch.events[0].kind, "message")

    async def test_handle_message_reports_error_and_still_logs(self):
        self.agent._events_enabled = True
        self.agent._schedule_telemetry = MagicMock()
        self.agent._logger = MagicMock()

        async def handler(_ctx, _sender, _msg):
            raise ValueError("handler failed")

        await self.agent._handle_message(
            handler, self._fake_context(), "agent1sender", MagicMock(), MagicMock()
        )

        # existing behavior: the exception is still logged
        self.agent._logger.exception.assert_called_once()
        # one received event + one error event
        self.assertEqual(self.agent._schedule_telemetry.call_count, 2)
        kinds = [c.args[0].events[0].kind for c in self.agent._schedule_telemetry.call_args_list]
        self.assertEqual(kinds, ["message", "error"])

    async def test_handle_message_no_telemetry_when_disabled(self):
        self.agent._events_enabled = False
        self.agent._schedule_telemetry = MagicMock()

        async def handler(_ctx, _sender, _msg):
            return None

        await self.agent._handle_message(
            handler, self._fake_context(), "agent1sender", MagicMock(), MagicMock()
        )
        self.agent._schedule_telemetry.assert_not_called()

    async def test_startup_dispatches_started_event(self):
        self.agent._update_agent_status = AsyncMock()
        dispatch_mock = AsyncMock()
        with (
            patch(
                "uagents.agent.is_registered_on_agentverse",
                AsyncMock(return_value=True),
            ),
            patch("uagents.agent.dispatch_events", dispatch_mock),
        ):
            await self.agent.run_startup_tasks()

        self.assertTrue(self.agent._events_enabled)
        dispatch_mock.assert_awaited_once()
        batch = dispatch_mock.await_args.args[2]
        self.assertEqual(batch.events[0].message, "Agent Started")

    async def test_shutdown_dispatches_stopped_event(self):
        self.agent._events_enabled = True
        dispatch_mock = AsyncMock()
        with patch("uagents.agent.dispatch_events", dispatch_mock):
            await self.agent.run_shutdown_tasks()

        dispatch_mock.assert_awaited_once()
        batch = dispatch_mock.await_args.args[2]
        self.assertEqual(batch.events[0].message, "Agent Stopped")

    async def test_shutdown_no_dispatch_when_disabled(self):
        self.agent._events_enabled = False
        dispatch_mock = AsyncMock()
        with patch("uagents.agent.dispatch_events", dispatch_mock):
            await self.agent.run_shutdown_tasks()
        dispatch_mock.assert_not_awaited()


class TestSentMessageTelemetry(unittest.IsolatedAsyncioTestCase):
    def _build_context(self, events_enabled: bool) -> InternalContext:
        agent = MagicMock()
        agent.identity = Identity.generate()
        agent.address = agent.identity.address
        return InternalContext(
            agent=agent,
            storage=MagicMock(),
            ledger=MagicMock(),
            resolver=MagicMock(),
            dispenser=MagicMock(),
            logger=MagicMock(),
            agentverse=AgentverseConfig(),
            events_enabled=events_enabled,
        )

    async def test_report_message_sent_when_enabled(self):
        ctx = self._build_context(events_enabled=True)
        dispatch_mock = AsyncMock()
        with patch("uagents.context.dispatch_events", dispatch_mock):
            ctx._report_message_sent("agent1recipient")
            # allow the fire-and-forget task to run
            for task in list(ctx._telemetry_tasks):
                await task

        dispatch_mock.assert_awaited_once()
        batch = dispatch_mock.await_args.args[2]
        event = batch.events[0]
        self.assertEqual(event.kind, "message")
        self.assertEqual(event.metadata["direction"], "sent")
        self.assertEqual(event.metadata["peer"], "agent1recipient")

    async def test_report_message_sent_noop_when_disabled(self):
        ctx = self._build_context(events_enabled=False)
        dispatch_mock = AsyncMock()
        with patch("uagents.context.dispatch_events", dispatch_mock):
            ctx._report_message_sent("agent1recipient")
        self.assertEqual(len(ctx._telemetry_tasks), 0)
        dispatch_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
