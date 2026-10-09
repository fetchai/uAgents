"""Tests for uagents_core.events — event schemas, FairEventBuffer, and dispatchers."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from uagents_core.events import (
    AgentBatchEvents,
    AgentEventsHandle,
    BatchEvent,
    EventIngestionOptions,
    EventsDispatcher,
    FairEventBuffer,
    MessageEventMetadata,
    PlatformMetadata,
    SharedEventsDispatcher,
    _build_error_event,
    _build_message_event,
    _utc_now,
)
from uagents_core.identity import Identity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _event(
    message: str = "test", category: str = "user", kind: str = "info"
) -> BatchEvent:
    return BatchEvent(
        category=category,
        kind=kind,
        timestamp=_utc_now(),
        message=message,
    )


def _identity() -> Identity:
    return Identity.from_seed("test-seed-for-events-unit-tests", 0)


# ---------------------------------------------------------------------------
# BatchEvent validation
# ---------------------------------------------------------------------------


class TestBatchEvent:
    def test_basic_info_event(self):
        event = _event("hello")
        assert event.kind == "info"
        assert event.message == "hello"
        assert event.id is not None

    def test_error_event_with_traceback(self):
        event = BatchEvent(
            category="system",
            kind="error",
            timestamp=_utc_now(),
            exception="RuntimeError",
            traceback="Traceback ...",
            message="something broke",
        )
        assert event.exception == "RuntimeError"

    def test_message_event_requires_valid_metadata(self):
        metadata = MessageEventMetadata(
            direction="received",
            peer="agent1qtest",
            msg_id=uuid4(),
            session_id=uuid4(),
        ).model_dump(mode="json")

        event = BatchEvent(
            category="user",
            kind="message",
            timestamp=_utc_now(),
            message="Message received from agent1qtest",
            metadata=metadata,
        )
        assert event.kind == "message"

    def test_message_event_rejects_invalid_metadata(self):
        with pytest.raises(Exception):
            BatchEvent(
                category="user",
                kind="message",
                timestamp=_utc_now(),
                message="bad metadata",
                metadata={"direction": "received", "peer": "agent1q"},
            )

    def test_message_event_allows_none_metadata(self):
        event = BatchEvent(
            category="user",
            kind="message",
            timestamp=_utc_now(),
            message="no metadata",
            metadata=None,
        )
        assert event.metadata is None


# ---------------------------------------------------------------------------
# AgentBatchEvents factory methods
# ---------------------------------------------------------------------------


class TestAgentBatchEvents:
    def test_from_message(self):
        batch = AgentBatchEvents.from_message("agent started")
        assert len(batch.events) == 1
        assert batch.events[0].kind == "info"
        assert batch.events[0].message == "agent started"

    def test_from_message_with_category_and_kind(self):
        batch = AgentBatchEvents.from_message("fail", "system", "error")
        assert batch.events[0].category == "system"
        assert batch.events[0].kind == "error"

    def test_from_message_sdk_version_is_keyword_only(self):
        batch = AgentBatchEvents.from_message(
            "test", "user", "info", sdk_version="custom-1.0"
        )
        assert batch.platform.sdk_version == "custom-1.0"

    def test_from_exception(self):
        exc = RuntimeError("boom")
        batch = AgentBatchEvents.from_exception(exc, "Traceback ...")
        assert len(batch.events) == 1
        assert batch.events[0].kind == "error"
        assert batch.events[0].exception == "RuntimeError"
        assert batch.events[0].message == "boom"
        assert batch.events[0].traceback == "Traceback ..."

    def test_from_exception_default_category_is_system(self):
        batch = AgentBatchEvents.from_exception(ValueError("x"), "tb")
        assert batch.events[0].category == "system"

    def test_from_exception_sdk_version_is_keyword_only(self):
        batch = AgentBatchEvents.from_exception(
            RuntimeError("x"), "tb", "user", sdk_version="v2"
        )
        assert batch.platform.sdk_version == "v2"
        assert batch.events[0].category == "user"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


class TestBuildHelpers:
    def test_build_message_event_received(self):
        event = _build_message_event("received", "agent1qpeer")
        assert event.kind == "message"
        assert event.category == "user"
        assert "received from" in event.message
        assert event.metadata["direction"] == "received"
        assert event.metadata["peer"] == "agent1qpeer"

    def test_build_message_event_sent(self):
        event = _build_message_event("sent", "agent1qpeer", session_id=uuid4())
        assert "sent to" in event.message
        assert event.metadata["session_id"] is not None

    def test_build_error_event(self):
        exc = ValueError("bad input")
        event = _build_error_event(exc, "Traceback ...")
        assert event.kind == "error"
        assert event.exception == "ValueError"
        assert event.message == "bad input"
        assert event.traceback == "Traceback ..."

    def test_build_error_event_custom_category(self):
        event = _build_error_event(RuntimeError("x"), "tb", category="system")
        assert event.category == "system"


# ---------------------------------------------------------------------------
# FairEventBuffer
# ---------------------------------------------------------------------------


class TestFairEventBuffer:
    @pytest.mark.asyncio
    async def test_push_and_pop(self):
        buffer = FairEventBuffer()
        event = _event("hello")
        assert buffer.push("agent-a", [event]) is True

        result = await buffer.pop(10)
        assert result is not None
        address, events = result
        assert address == "agent-a"
        assert len(events) == 1
        assert events[0].message == "hello"

    @pytest.mark.asyncio
    async def test_round_robin_order(self):
        buffer = FairEventBuffer()
        buffer.push("agent-a", [_event("a1")])
        buffer.push("agent-b", [_event("b1")])
        buffer.push("agent-a", [_event("a2")])

        result1 = await buffer.pop(10)
        assert result1[0] == "agent-a"
        assert len(result1[1]) == 2

        result2 = await buffer.pop(10)
        assert result2[0] == "agent-b"
        assert len(result2[1]) == 1

    @pytest.mark.asyncio
    async def test_pop_respects_max_events(self):
        buffer = FairEventBuffer()
        buffer.push("agent-a", [_event(f"e{i}") for i in range(5)])

        result = await buffer.pop(2)
        assert result is not None
        _, events = result
        assert len(events) == 2

        result2 = await buffer.pop(10)
        assert result2 is not None
        assert result2[0] == "agent-a"
        assert len(result2[1]) == 3

    @pytest.mark.asyncio
    async def test_overflow_drops_and_reports(self):
        buffer = FairEventBuffer(per_agent_cap=2)
        buffer.push("agent-a", [_event("e1"), _event("e2")])
        buffer.push("agent-a", [_event("e3"), _event("e4")])

        result = await buffer.pop(10)
        assert result is not None
        _, events = result
        # 2 kept events + 1 drop notification = 3 total
        # pop reserves 1 slot for the drop notification (max_events - 1 for data)
        assert len(events) == 3
        kept_messages = [
            e.message for e in events if e.message and "dropped" not in e.message
        ]
        drop_events = [e for e in events if e.message and "dropped" in e.message]
        assert len(kept_messages) == 2
        assert len(drop_events) == 1
        assert drop_events[0].metadata["dropped_count"] == 2

    @pytest.mark.asyncio
    async def test_push_returns_false_after_shutdown(self):
        buffer = FairEventBuffer()
        buffer.shutdown()
        assert buffer.push("agent-a", [_event("late")]) is False

    @pytest.mark.asyncio
    async def test_shutdown_returns_none_when_empty(self):
        buffer = FairEventBuffer()
        buffer.shutdown()
        result = await buffer.pop(10)
        assert result is None

    @pytest.mark.asyncio
    async def test_shutdown_drains_remaining_events(self):
        buffer = FairEventBuffer()
        buffer.push("agent-a", [_event("drain-me")])
        buffer.shutdown()

        result = await buffer.pop(10)
        assert result is not None
        assert result[0] == "agent-a"
        assert result[1][0].message == "drain-me"

        result2 = await buffer.pop(10)
        assert result2 is None

    @pytest.mark.asyncio
    async def test_pop_blocks_until_push(self):
        buffer = FairEventBuffer()

        async def delayed_push():
            await asyncio.sleep(0.05)
            buffer.push("agent-a", [_event("delayed")])

        asyncio.create_task(delayed_push())
        result = await buffer.pop(10, timeout=1.0)
        assert result is not None
        assert result[1][0].message == "delayed"

    @pytest.mark.asyncio
    async def test_pop_while_loop_retries_on_spurious_wake(self):
        """pop() uses while (not if), so a spurious wake with no data loops back."""
        buffer = FairEventBuffer()

        async def spurious_then_real():
            await asyncio.sleep(0.02)
            buffer._wake.set()
            await asyncio.sleep(0.05)
            buffer.push("agent-a", [_event("real")])

        asyncio.create_task(spurious_then_real())
        result = await buffer.pop(10, timeout=0.5)
        assert result is not None
        assert result[1][0].message == "real"

    def test_push_empty_list_returns_true(self):
        buffer = FairEventBuffer()
        assert buffer.push("agent-a", []) is True

    @pytest.mark.asyncio
    async def test_is_shutdown_property(self):
        buffer = FairEventBuffer()
        assert buffer.is_shutdown is False
        buffer.shutdown()
        assert buffer.is_shutdown is True


# ---------------------------------------------------------------------------
# EventsDispatcher
# ---------------------------------------------------------------------------


class TestEventsDispatcher:
    def _make_dispatcher(self, **option_overrides) -> EventsDispatcher:
        from uagents_core.config import AgentverseConfig

        options = EventIngestionOptions(**option_overrides)
        agentverse = AgentverseConfig(base_url="localhost:8000", http_prefix="http")
        return EventsDispatcher(
            identity=_identity(),
            agentverse=agentverse,
            options=options,
        )

    def test_enqueue_buffers_events(self):
        dispatcher = self._make_dispatcher()
        dispatcher.enqueue([_event("e1")])
        assert dispatcher._queue.qsize() == 1

    def test_enqueue_drops_on_overflow(self):
        dispatcher = self._make_dispatcher(max_batch_events=1)
        dispatcher.enqueue([_event("first"), _event("second")])
        assert dispatcher._queue.qsize() == 1
        assert dispatcher._dropped_events_count == 1

    def test_enqueue_ignores_empty_list(self):
        dispatcher = self._make_dispatcher()
        dispatcher.enqueue([])
        assert dispatcher._queue.qsize() == 0

    def test_enqueue_drops_during_shutdown(self):
        dispatcher = self._make_dispatcher()
        dispatcher._stopping = True
        dispatcher.enqueue([_event("late")])
        assert dispatcher._queue.qsize() == 0

    def test_report_message_enqueues(self):
        dispatcher = self._make_dispatcher()
        dispatcher.report_message("received", "agent1qpeer")
        assert dispatcher._queue.qsize() == 1
        event = dispatcher._queue.get_nowait()
        assert event.kind == "message"

    def test_report_exception_enqueues(self):
        dispatcher = self._make_dispatcher()
        dispatcher.report_exception(ValueError("oops"), "tb", "user")
        assert dispatcher._queue.qsize() == 1
        event = dispatcher._queue.get_nowait()
        assert event.kind == "error"
        assert event.exception == "ValueError"

    @pytest.mark.asyncio
    async def test_worker_posts_events(self):
        dispatcher = self._make_dispatcher(flush_interval_s=0.01)
        posted = []

        await dispatcher.start()

        async def capture_post(url, *, content, headers):
            posted.append(content)

        with patch.object(dispatcher._transport, "post", side_effect=capture_post):
            dispatcher.enqueue([_event("hello")])
            await asyncio.sleep(0.15)

        await dispatcher.stop()

        assert posted
        batch = AgentBatchEvents.model_validate_json(posted[0])
        assert batch.events[0].message == "hello"

    @pytest.mark.asyncio
    async def test_drop_notification_prepended(self):
        dispatcher = self._make_dispatcher(max_batch_events=50, flush_interval_s=0.01)
        posted = []

        await dispatcher.start()

        async def capture_post(url, *, content, headers):
            posted.append(content)

        with patch.object(dispatcher._transport, "post", side_effect=capture_post):
            dispatcher._dropped_events_count = 3
            dispatcher._first_drop_at = _utc_now()
            dispatcher.enqueue([_event("after-drops")])
            await asyncio.sleep(0.15)

        await dispatcher.stop()

        assert posted
        batch = AgentBatchEvents.model_validate_json(posted[0])
        assert batch.events[0].metadata["dropped_count"] == 3
        assert batch.events[1].message == "after-drops"

    @pytest.mark.asyncio
    async def test_coalesces_events_in_order(self):
        dispatcher = self._make_dispatcher(flush_interval_s=0.01, max_batch_events=10)
        posted = []

        await dispatcher.start()

        async def capture_post(url, *, content, headers):
            posted.append(content)

        with patch.object(dispatcher._transport, "post", side_effect=capture_post):
            dispatcher.enqueue([_event("one")])
            dispatcher.enqueue([_event("two")])
            await asyncio.sleep(0.15)

        await dispatcher.stop()

        assert posted
        batch = AgentBatchEvents.model_validate_json(posted[0])
        messages = [e.message for e in batch.events]
        assert messages == ["one", "two"]

    @pytest.mark.asyncio
    async def test_stop_drains_remaining_events(self):
        dispatcher = self._make_dispatcher(flush_interval_s=0.01)
        posted = []

        await dispatcher.start()

        async def capture_post(url, *, content, headers):
            posted.append(content)

        with patch.object(dispatcher._transport, "post", side_effect=capture_post):
            dispatcher.enqueue([_event("drain-me")])
            await dispatcher.stop()

        assert any("drain-me" in p for p in posted), (
            "Event should be posted during drain"
        )

    @pytest.mark.asyncio
    async def test_address_property(self):
        dispatcher = self._make_dispatcher()
        assert dispatcher.address == _identity().address


# ---------------------------------------------------------------------------
# SharedEventsDispatcher
# ---------------------------------------------------------------------------


class TestSharedEventsDispatcher:
    @pytest.mark.asyncio
    async def test_fair_dispatch_across_agents(self):
        from uagents_core.config import AgentverseConfig

        agentverse = AgentverseConfig(base_url="localhost:8000", http_prefix="http")
        options = EventIngestionOptions(flush_interval_s=0.01)
        shared = SharedEventsDispatcher(agentverse=agentverse, options=options)

        identity_a = Identity.from_seed("seed-a", 0)
        identity_b = Identity.from_seed("seed-b", 0)

        dispatcher_a = EventsDispatcher(identity=identity_a, agentverse=agentverse)
        dispatcher_b = EventsDispatcher(identity=identity_b, agentverse=agentverse)

        handle_a = shared.add_agent(dispatcher_a)
        handle_b = shared.add_agent(dispatcher_b)

        posted_addresses = []

        original_post = dispatcher_a._post

        async def capture_post_a(events):
            posted_addresses.append(identity_a.address)

        async def capture_post_b(events):
            posted_addresses.append(identity_b.address)

        dispatcher_a._post = capture_post_a
        dispatcher_b._post = capture_post_b

        handle_a.enqueue([_event("a1")])
        handle_b.enqueue([_event("b1")])
        handle_a.enqueue([_event("a2")])

        run_task = asyncio.create_task(shared.run())
        await asyncio.sleep(0.15)
        shared.stop()
        await run_task

        assert identity_a.address in posted_addresses
        assert identity_b.address in posted_addresses
        assert posted_addresses[0] == identity_a.address
        assert posted_addresses[1] == identity_b.address


# ---------------------------------------------------------------------------
# AgentEventsHandle
# ---------------------------------------------------------------------------


class TestAgentEventsHandle:
    def test_report_message_pushes_to_buffer(self):
        from uagents_core.config import AgentverseConfig

        agentverse = AgentverseConfig(base_url="localhost:8000", http_prefix="http")
        identity = _identity()
        dispatcher = EventsDispatcher(identity=identity, agentverse=agentverse)
        buffer = FairEventBuffer()
        handle = AgentEventsHandle(dispatcher, buffer)

        handle.report_message("received", "agent1qpeer")
        assert identity.address in buffer._buffers
        assert len(buffer._buffers[identity.address]) == 1
        assert buffer._buffers[identity.address][0].kind == "message"

    def test_report_exception_pushes_to_buffer(self):
        from uagents_core.config import AgentverseConfig

        agentverse = AgentverseConfig(base_url="localhost:8000", http_prefix="http")
        identity = _identity()
        dispatcher = EventsDispatcher(identity=identity, agentverse=agentverse)
        buffer = FairEventBuffer()
        handle = AgentEventsHandle(dispatcher, buffer)

        handle.report_exception(RuntimeError("boom"), "Traceback ...")
        assert identity.address in buffer._buffers
        assert buffer._buffers[identity.address][0].kind == "error"

    def test_enqueue_silently_drops_after_shutdown(self):
        from uagents_core.config import AgentverseConfig

        agentverse = AgentverseConfig(base_url="localhost:8000", http_prefix="http")
        dispatcher = EventsDispatcher(identity=_identity(), agentverse=agentverse)
        buffer = FairEventBuffer()
        handle = AgentEventsHandle(dispatcher, buffer)

        buffer.shutdown()
        handle.enqueue([_event("too late")])
        assert not buffer._buffers

    def test_address_property(self):
        from uagents_core.config import AgentverseConfig

        agentverse = AgentverseConfig(base_url="localhost:8000", http_prefix="http")
        identity = _identity()
        dispatcher = EventsDispatcher(identity=identity, agentverse=agentverse)
        buffer = FairEventBuffer()
        handle = AgentEventsHandle(dispatcher, buffer)

        assert handle.address == identity.address


# ---------------------------------------------------------------------------
# PlatformMetadata
# ---------------------------------------------------------------------------


class TestPlatformMetadata:
    def test_current_collects_platform_info(self):
        meta = PlatformMetadata.current()
        assert meta.python_version
        assert meta.operating_system.name
        assert meta.sdk_version

    def test_current_accepts_custom_sdk_version(self):
        meta = PlatformMetadata.current(sdk_version="custom-1.0.0")
        assert meta.sdk_version == "custom-1.0.0"
