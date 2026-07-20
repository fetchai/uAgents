# pylint: disable=protected-access
import asyncio
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
    EventIngestionOptions,
    EventsDispatcher,
    MessageEventMetadata,
    MultiAgentEventsDispatcher,
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
        self.agent._events_dispatcher = MagicMock()

        async def handler(_ctx, _sender, _msg):
            return None

        await self.agent._handle_message(
            handler, self._fake_context(), "agent1sender", MagicMock(), MagicMock()
        )

        self.agent._events_dispatcher.report_message.assert_called_once()
        args = self.agent._events_dispatcher.report_message.call_args.args
        self.assertEqual(args[0], "received")
        self.assertEqual(args[1], "agent1sender")

    async def test_handle_message_reports_error_and_still_logs(self):
        self.agent._events_enabled = True
        self.agent._events_dispatcher = MagicMock()
        self.agent._logger = MagicMock()

        async def handler(_ctx, _sender, _msg):
            raise ValueError("handler failed")

        await self.agent._handle_message(
            handler, self._fake_context(), "agent1sender", MagicMock(), MagicMock()
        )

        # existing behavior: the exception is still logged
        self.agent._logger.exception.assert_called_once()
        # one received (message) event + one handler-error event
        self.agent._events_dispatcher.report_message.assert_called_once()
        self.agent._events_dispatcher.report_exception.assert_called_once()

    async def test_handle_message_no_telemetry_when_disabled(self):
        self.agent._events_enabled = False
        self.agent._events_dispatcher = MagicMock()

        async def handler(_ctx, _sender, _msg):
            return None

        await self.agent._handle_message(
            handler, self._fake_context(), "agent1sender", MagicMock(), MagicMock()
        )
        self.agent._events_dispatcher.report_message.assert_not_called()

    async def test_startup_starts_dispatcher_and_dispatches_started_event(self):
        self.agent._update_agent_status = AsyncMock()
        dispatch_mock = AsyncMock()
        dispatcher_instance = MagicMock()
        dispatcher_instance.start = AsyncMock()
        dispatcher_cls = MagicMock(return_value=dispatcher_instance)
        with (
            patch(
                "uagents.agent.is_registered_on_agentverse",
                AsyncMock(return_value=True),
            ),
            patch("uagents.agent.EventsDispatcher", dispatcher_cls),
            patch("uagents.agent.dispatch_events", dispatch_mock),
        ):
            await self.agent.run_startup_tasks()

        self.assertTrue(self.agent._events_enabled)
        dispatcher_instance.start.assert_awaited_once()
        dispatch_mock.assert_awaited_once()
        batch = dispatch_mock.await_args.args[2]
        self.assertEqual(batch.events[0].message, "Agent Started")

    async def test_shutdown_dispatches_stopped_event_and_drains_dispatcher(self):
        self.agent._events_enabled = True
        self.agent._events_dispatcher = MagicMock()
        self.agent._events_dispatcher.stop = AsyncMock()
        dispatch_mock = AsyncMock()
        with patch("uagents.agent.dispatch_events", dispatch_mock):
            await self.agent.run_shutdown_tasks()

        dispatch_mock.assert_awaited_once()
        batch = dispatch_mock.await_args.args[2]
        self.assertEqual(batch.events[0].message, "Agent Stopped")
        # dispatcher is drained and cleared on shutdown
        self.assertIsNone(self.agent._events_dispatcher)

    async def test_shutdown_no_dispatch_when_disabled(self):
        self.agent._events_enabled = False
        dispatch_mock = AsyncMock()
        with patch("uagents.agent.dispatch_events", dispatch_mock):
            await self.agent.run_shutdown_tasks()
        dispatch_mock.assert_not_awaited()


class TestSentMessageTelemetry(unittest.IsolatedAsyncioTestCase):
    def _build_context(self, events_dispatcher) -> InternalContext:
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
            events_dispatcher=events_dispatcher,
        )

    async def test_report_message_sent_when_enabled(self):
        dispatcher = MagicMock()
        ctx = self._build_context(dispatcher)
        ctx._report_message_sent("agent1recipient")
        dispatcher.report_message.assert_called_once_with(
            "sent", "agent1recipient", ctx._session
        )

    async def test_report_message_sent_noop_when_disabled(self):
        ctx = self._build_context(None)
        # Must not raise when no dispatcher is configured.
        ctx._report_message_sent("agent1recipient")


def _mock_persistent_client(response=None, post_side_effect=None):
    """Build a mock for the dispatcher's long-lived httpx.AsyncClient."""
    client = MagicMock()
    if post_side_effect is not None:
        client.post = AsyncMock(side_effect=post_side_effect)
    else:
        client.post = AsyncMock(return_value=response)
    client.aclose = AsyncMock()
    return MagicMock(return_value=client), client


class TestEventsDispatcher(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.identity = Identity.generate()
        self.agentverse = AgentverseConfig()

    def _ok_response(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        return response

    async def test_enqueue_and_flush_posts_to_events_endpoint(self):
        factory, client = _mock_persistent_client(response=self._ok_response())
        with patch("uagents_core.events.httpx.AsyncClient", factory):
            dispatcher = EventsDispatcher(self.identity, self.agentverse)
            await dispatcher.start()
            dispatcher.report_message("sent", "agent1peer")
            await dispatcher.stop()

        client.post.assert_awaited()
        url = client.post.await_args.args[0]
        self.assertTrue(url.endswith("/v1/events"))
        client.aclose.assert_awaited_once()

    async def test_retries_on_transient_failure(self):
        factory, client = _mock_persistent_client(
            post_side_effect=[httpx.ConnectError("down"), self._ok_response()]
        )
        options = EventIngestionOptions(retry_base_delay_s=0.01, flush_interval_s=0.02)
        with patch("uagents_core.events.httpx.AsyncClient", factory):
            dispatcher = EventsDispatcher(self.identity, self.agentverse, options)
            await dispatcher.start()
            dispatcher.enqueue(AgentBatchEvents.from_message("retry me"))
            await asyncio.sleep(0.2)
            await dispatcher.stop()

        self.assertGreaterEqual(client.post.await_count, 2)

    async def test_drops_and_accounts_when_queue_full(self):
        # maxsize=1 and no worker running: second/third enqueue are dropped.
        dispatcher = EventsDispatcher(
            self.identity,
            self.agentverse,
            EventIngestionOptions(queue_max_batches=1),
        )
        dispatcher.enqueue(AgentBatchEvents.from_message("one"))
        dispatcher.enqueue(AgentBatchEvents.from_message("two"))
        dispatcher.enqueue(AgentBatchEvents.from_message("three"))
        self.assertEqual(dispatcher._dropped_events_count, 2)

    async def test_stop_is_noop_when_never_started(self):
        dispatcher = EventsDispatcher(self.identity, self.agentverse)
        # Must not raise even though start() was never called.
        await dispatcher.stop()

    async def test_events_url_uses_agentverse_events_api(self):
        dispatcher = EventsDispatcher(self.identity, self.agentverse)
        self.assertEqual(dispatcher.events_url, self.agentverse.events_api)
        self.assertTrue(dispatcher.events_url.endswith("/v1/events"))


class TestMultiAgentEventsDispatcher(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agentverse = AgentverseConfig()
        self.alice = Identity.generate()
        self.bob = Identity.generate()

    def _ok_response(self):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        return response

    async def test_separate_posts_for_different_identities(self):
        """Different agents in one queue must not share a single attested POST."""
        factory, client = _mock_persistent_client(response=self._ok_response())
        options = EventIngestionOptions(flush_interval_s=0.05, max_batch_events=50)
        with patch("uagents_core.events.httpx.AsyncClient", factory):
            dispatcher = MultiAgentEventsDispatcher(self.agentverse, options)
            await dispatcher.start()
            dispatcher.enqueue_event(
                self.alice, AgentBatchEvents.from_message("from alice")
            )
            dispatcher.enqueue_event(
                self.bob, AgentBatchEvents.from_message("from bob")
            )
            await asyncio.sleep(0.2)
            await dispatcher.stop()

        self.assertGreaterEqual(client.post.await_count, 2)
        contents = [c.kwargs["content"] for c in client.post.await_args_list]
        messages = []
        for content in contents:
            batch = AgentBatchEvents.model_validate_json(content)
            messages.extend(e.message for e in batch.events)
        self.assertIn("from alice", messages)
        self.assertIn("from bob", messages)
        # No merged POST should contain both agents' user messages together.
        for content in contents:
            batch = AgentBatchEvents.model_validate_json(content)
            user_messages = {
                e.message
                for e in batch.events
                if e.message in {"from alice", "from bob"}
            }
            self.assertLessEqual(len(user_messages), 1)

    async def test_coalesces_same_identity_only(self):
        factory, client = _mock_persistent_client(response=self._ok_response())
        options = EventIngestionOptions(flush_interval_s=0.1, max_batch_events=50)
        with patch("uagents_core.events.httpx.AsyncClient", factory):
            dispatcher = MultiAgentEventsDispatcher(self.agentverse, options)
            await dispatcher.start()
            dispatcher.enqueue_event(
                self.alice, AgentBatchEvents.from_message("alice-1")
            )
            dispatcher.enqueue_event(
                self.alice, AgentBatchEvents.from_message("alice-2")
            )
            await asyncio.sleep(0.25)
            await dispatcher.stop()

        # Same identity may be coalesced into one POST with both messages.
        contents = [c.kwargs["content"] for c in client.post.await_args_list]
        found_both = False
        for content in contents:
            msgs = {e.message for e in AgentBatchEvents.model_validate_json(content).events}
            if {"alice-1", "alice-2"} <= msgs:
                found_both = True
        self.assertTrue(found_both or client.post.await_count >= 2)


if __name__ == "__main__":
    unittest.main()
