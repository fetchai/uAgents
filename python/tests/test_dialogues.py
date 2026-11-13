"""Local dialogue expiry is independent of cleanup scheduling."""

from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from uagents_core.types import DeliveryStatus

from uagents import Model
from uagents.context import ExternalContext
from uagents.experimental.dialogues import Dialogue, Edge, Node, _DialogueContext


class Start(Model):
    pass


class Reply(Model):
    pass


class MemoryStore:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return deepcopy(self.data.get(key))

    def set(self, key, value):
        self.data[key] = deepcopy(value)


@pytest.fixture
def clock():
    with patch("uagents.experimental.dialogues.time", return_value=1000.0) as mocked:
        # Also control the upstream implementation's clock for regression checks.
        class ClockDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls.fromtimestamp(mocked.return_value, tz)

        with patch(
            "uagents.experimental.dialogues.datetime", ClockDatetime, create=True
        ):
            yield mocked


def make_dialogue(store=None, timeout=60, interval=1):
    first, last = Node("first", "First"), Node("last", "Last")
    start = Edge("start", "Start", None, first)
    reply = Edge("reply", "Reply", first, last)
    start.model, reply.model = Start, Reply

    async def noop(ctx, sender, message):
        pass

    start.func = reply.func = noop
    return Dialogue(
        "test",
        storage=store or MemoryStore(),
        nodes=[first, last],
        edges=[start, reply],
        timeout=timeout,
        cleanup_interval=interval,
    )


def seed(dialogue):
    session = uuid4()
    digest = Model.build_schema_digest(Start)
    dialogue.add_message(session, "Start", digest, "alice", "bob", "{}")
    dialogue.update_state(digest, session)
    return session


@pytest.mark.parametrize("interval", [0, 1, 30])
def test_expiry_boundary_independent_of_cleanup(clock, interval):
    dialogue = make_dialogue(interval=interval)
    session = seed(dialogue)
    digest = Model.build_schema_digest(Reply)
    clock.return_value = 1059
    assert dialogue.is_valid_message(session, digest)
    clock.return_value = 1060
    assert not dialogue.is_valid_message(session, digest)
    assert session in dialogue._sessions


def test_restart_preserves_deadline_and_removes_expired_state(clock):
    store = MemoryStore()
    dialogue = make_dialogue(store)
    session = seed(dialogue)
    clock.return_value = 1059
    restored = make_dialogue(store)
    assert restored.is_valid_message(session, Model.build_schema_digest(Reply))
    clock.return_value = 1060
    restored = make_dialogue(store)
    assert session not in restored._sessions
    assert restored.get_current_state(session) == ""
    assert str(session) not in store.get("test")


def test_unlimited_and_empty_sessions_survive_restart(clock):
    store = MemoryStore()
    dialogue = make_dialogue(store, timeout=0)
    session = seed(dialogue)
    empty = uuid4()
    store.set("test", store.get("test") | {str(empty): []})
    clock.return_value = 1000000
    restored = make_dialogue(store, timeout=0)
    assert not restored.is_expired(session)
    assert restored.is_valid_message(session, Model.build_schema_digest(Reply))
    assert empty in restored._sessions


@pytest.mark.asyncio
async def test_cleanup_is_complete_repeatable_and_handles_empty_sessions(clock):
    dialogue = make_dialogue()
    session = seed(dialogue)
    empty = uuid4()
    dialogue._add_session(empty)
    clock.return_value = 1060
    await dialogue.intervals[0][0](None)
    dialogue.cleanup_conversation(session)
    assert session not in dialogue._sessions
    assert dialogue.get_current_state(session) == ""
    assert str(session) not in dialogue._storage.get("test")
    assert empty in dialogue._sessions


@pytest.mark.asyncio
async def test_expired_inbound_never_runs_handler(clock):
    dialogue = make_dialogue()
    session = seed(dialogue)
    handler = AsyncMock()
    wrapped = dialogue._on_state_transition("reply", Reply)(handler)
    ctx = SimpleNamespace(session=session, send=AsyncMock())
    clock.return_value = 1060
    await wrapped(ctx, "alice", Reply())
    handler.assert_not_awaited()
    assert ctx.send.call_args.args[1].error == "Dialogue session expired"


@pytest.mark.asyncio
async def test_handler_crossing_deadline_cannot_send_or_restore_cleaned_session(clock):
    dialogue = make_dialogue()
    session = uuid4()
    ctx = object.__new__(ExternalContext)
    ctx._session = session
    ctx._agent = SimpleNamespace(address="bob")
    ctx._protocol = ("test", None)
    ctx._queries = {}
    ctx._outbound_messages = {}

    @dialogue._on_state_transition("start", Start)
    async def handler(context, sender, message):
        clock.return_value = 1060
        await dialogue.intervals[0][0](None)
        status = await context.send(sender, Reply())
        assert status.status == DeliveryStatus.FAILED
        assert status.detail == "Dialogue session expired"

    with patch.object(ExternalContext, "send_raw", new_callable=AsyncMock) as dispatch:
        status = await handler(ctx, "alice", Start())
    dispatch.assert_not_awaited()
    assert status.detail == "Dialogue session expired"
    assert session not in dialogue._sessions


@pytest.mark.asyncio
async def test_send_guard_allows_active_and_unlimited_sessions(clock):
    base = object.__new__(ExternalContext)
    base._session = uuid4()
    with patch.object(ExternalContext, "send_raw", new_callable=AsyncMock) as dispatch:
        await _DialogueContext(base, 1060).send_raw("alice", "digest", "{}")
        clock.return_value = 2000
        await _DialogueContext(base, None).send_raw("alice", "digest", "{}")
    assert dispatch.await_count == 2


@pytest.mark.asyncio
async def test_expired_raw_send_never_dispatches(clock):
    base = object.__new__(ExternalContext)
    base._session = uuid4()
    clock.return_value = 1060
    with patch.object(ExternalContext, "send_raw", new_callable=AsyncMock) as dispatch:
        status = await _DialogueContext(base, 1060).send_raw("alice", "digest", "{}")
    dispatch.assert_not_awaited()
    assert status.status == DeliveryStatus.FAILED


@pytest.mark.asyncio
async def test_start_cannot_reuse_expired_session(clock):
    dialogue = make_dialogue()
    session = seed(dialogue)
    ctx = SimpleNamespace(session=session, send=AsyncMock(), broadcast=AsyncMock())
    clock.return_value = 1060
    statuses = await dialogue.start_dialogue(ctx, "agent-test", Start())
    assert statuses[0].detail == "Dialogue session expired"
    ctx.send.assert_not_awaited()
    ctx.broadcast.assert_not_awaited()


@pytest.mark.asyncio
async def test_active_handler_reply_updates_shared_history_and_idle_deadline(clock):
    dialogue = make_dialogue()
    session = uuid4()
    ctx = object.__new__(ExternalContext)
    ctx._session = session
    ctx._agent = SimpleNamespace(address="bob")
    ctx._protocol = ("test", None)
    ctx._queries = {}
    ctx._outbound_messages = {}

    @dialogue._on_state_transition("start", Start)
    async def handler(context, sender, message):
        clock.return_value = 1030
        await context.send(sender, Reply())

    async def dispatch(destination, message_schema_digest, message_body, **kwargs):
        ctx._outbound_messages[destination] = [(message_body, message_schema_digest)]

    with patch.object(ExternalContext, "send_raw", side_effect=dispatch):
        await handler(ctx, "alice", Start())
    assert len(dialogue.get_conversation(session)) == 2
    assert dialogue.is_finished(session)
    assert "alice" in ctx.outbound_messages
    clock.return_value = 1089
    assert not dialogue.is_expired(session)
    clock.return_value = 1090
    assert dialogue.is_expired(session)
