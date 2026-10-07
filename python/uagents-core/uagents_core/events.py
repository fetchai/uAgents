"""
Telemetry events for Agentverse-registered agents.

This module defines the event schema understood by the Agentverse events API
(``POST {agentverse.url}/v1/events``) together with the helpers used to
authenticate against, dispatch events to, and query the registration status
from Agentverse.

Telemetry must never interfere with agent logic: :func:`dispatch_events` and
:func:`is_registered_on_agentverse` swallow every error (failing closed) and
never raise into the caller.
"""

import asyncio
import contextlib
import logging
import platform
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from importlib.metadata import version as _package_version
from secrets import token_bytes
from typing import Any, Literal
from uuid import UUID, uuid4

import httpx
from pydantic import BaseModel, Field, model_validator

from uagents_core.config import AgentverseConfig
from uagents_core.identity import Identity
from uagents_core.storage import compute_attestation
from uagents_core.transport import RetryTransport

# httpx logs every successful request at INFO by default; telemetry POSTs would
# spam agent consoles. Raise the threshold so those stay out of normal output
# (still visible if the app forces the httpx logger down to DEBUG explicitly).
logging.getLogger("httpx").setLevel(logging.WARNING)

EventCategory = Literal["system", "user"]
EventKind = Literal["error", "info", "message"]
MessageDirection = Literal["received", "sent"]

# Attestation tokens for telemetry requests are short-lived by design.
AUTH_TOKEN_VALIDITY_SECS = 120

# Default HTTP timeout (seconds) for telemetry requests.
DEFAULT_EVENTS_HTTP_TIMEOUT_S = 10

# Defaults for the background events dispatcher.
DEFAULT_EVENTS_QUEUE_MAX_BATCHES = 256
DEFAULT_EVENTS_FLUSH_INTERVAL_S = 0.1
DEFAULT_EVENTS_MAX_BATCH_EVENTS = 50
DEFAULT_EVENTS_RETRY_BASE_DELAY_S = 1.0
DEFAULT_EVENTS_MAX_RETRY_DELAY_S = 30.0
DEFAULT_EVENTS_SHUTDOWN_DRAIN_TIMEOUT_S = 5.0


# Resolved once at import time and used as the default for event metadata so
# callers (e.g. the uAgents runtime) don't need to compute or thread it through.
DEFAULT_SDK_VERSION = _package_version("uagents-core")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OperatingSystemMetadata(BaseModel):
    name: str
    version: str
    release: str


class PlatformMetadata(BaseModel):
    operating_system: OperatingSystemMetadata
    python_version: str
    processor: str
    nodename: str
    sdk_version: str

    @classmethod
    def current(cls, sdk_version: str = DEFAULT_SDK_VERSION) -> "PlatformMetadata":
        """Collect platform metadata for the running process."""
        return cls(
            operating_system=OperatingSystemMetadata(
                name=platform.system(),
                version=platform.version(),
                release=platform.release(),
            ),
            python_version=platform.python_version(),
            processor=platform.processor(),
            nodename=platform.node(),
            sdk_version=sdk_version,
        )


PLATFORM_METADATA = PlatformMetadata.current()


class MessageEventMetadata(BaseModel):
    direction: MessageDirection
    peer: str = Field(max_length=66)
    msg_id: UUID
    session_id: UUID | None = None


class BatchEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)  # client-assigned; server dedups on it
    category: EventCategory
    kind: EventKind
    timestamp: datetime
    exception: str | None = None  # exception class qualname (error events)
    traceback: str | None = None  # full traceback string (error events)
    metadata: dict[str, Any] | None = None  # for kind="message": MessageEventMetadata
    message: str | None = None  # human-readable summary

    @model_validator(mode="after")
    def _validate_message_metadata(self) -> "BatchEvent":
        if self.kind == "message" and self.metadata is not None:
            MessageEventMetadata.model_validate(self.metadata)
        return self


class AgentBatchEvents(BaseModel):
    platform: PlatformMetadata
    events: list[BatchEvent]

    @classmethod
    def from_message(
        cls,
        message: str,
        category: EventCategory = "user",
        kind: EventKind = "info",
        metadata: dict[str, Any] | None = None,
        *,
        sdk_version: str = DEFAULT_SDK_VERSION,
    ) -> "AgentBatchEvents":
        """Build a single-event batch describing an informational message."""
        return cls(
            platform=PlatformMetadata.current(sdk_version),
            events=[
                BatchEvent(
                    category=category,
                    kind=kind,
                    timestamp=_utc_now(),
                    message=message,
                    metadata=metadata,
                )
            ],
        )

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        traceback: str,
        category: EventCategory = "system",
        *,
        sdk_version: str = DEFAULT_SDK_VERSION,
    ) -> "AgentBatchEvents":
        """Build a single-event batch describing an error/exception."""
        return cls(
            platform=PlatformMetadata.current(sdk_version),
            events=[
                BatchEvent(
                    category=category,
                    kind="error",
                    timestamp=_utc_now(),
                    exception=exception.__class__.__qualname__,
                    traceback=traceback,
                    message=str(exception),
                )
            ],
        )


def _auth_header(identity: Identity) -> dict[str, str]:
    """Build the ``Authorization: Agent <attestation>`` header for a request."""
    token = compute_attestation(
        identity, _utc_now(), AUTH_TOKEN_VALIDITY_SECS, token_bytes(32)
    )
    return {"Authorization": f"Agent {token}", "Content-Type": "application/json"}


async def dispatch_events(
    identity: Identity,
    agentverse: AgentverseConfig,
    events: AgentBatchEvents,
    *,
    logger: logging.Logger | None = None,
    timeout: int = DEFAULT_EVENTS_HTTP_TIMEOUT_S,
) -> None:
    """
    POST a batch of events to the Agentverse events API.

    Failures are swallowed (and optionally logged at debug level): telemetry
    must never crash or interfere with the agent.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                agentverse.events_api,
                content=events.model_dump_json(),
                headers=_auth_header(identity),
            )
            response.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - telemetry must never raise
        if logger is not None:
            logger.debug(f"Failed to dispatch telemetry events: {exc}")


async def is_registered_on_agentverse(
    identity: Identity,
    agentverse: AgentverseConfig,
    *,
    timeout: int = 10,
) -> bool:
    """
    Check whether the agent is registered on Agentverse.

    Performs ``GET {agentverse.agents_api}/{address}``; a ``200`` response means
    the agent is registered. Any other status or a network error is treated as
    "not registered" (fail closed).
    """
    url = f"{agentverse.agents_api}/{identity.address}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=_auth_header(identity))
    except httpx.HTTPError:
        return False
    return response.status_code == 200


class EventIngestionOptions(BaseModel):
    """Tuning knobs for the events dispatchers."""

    queue_max_batches: int = Field(default=DEFAULT_EVENTS_QUEUE_MAX_BATCHES, ge=1)
    flush_interval_s: float = Field(default=DEFAULT_EVENTS_FLUSH_INTERVAL_S, gt=0)
    max_batch_events: int = Field(default=DEFAULT_EVENTS_MAX_BATCH_EVENTS, ge=1)
    retry_base_delay_s: float = Field(default=DEFAULT_EVENTS_RETRY_BASE_DELAY_S, gt=0)
    max_retry_delay_s: float = Field(default=DEFAULT_EVENTS_MAX_RETRY_DELAY_S, gt=0)
    shutdown_drain_timeout_s: float = Field(
        default=DEFAULT_EVENTS_SHUTDOWN_DRAIN_TIMEOUT_S, gt=0
    )


class FairEventBuffer:
    """Per-agent event buffer with round-robin scheduling.

    Events are grouped by agent address.  ``pop`` cycles through
    agents so no single agent can starve others, regardless of
    how many events it produces.
    """

    def __init__(
        self,
        per_agent_cap: int = DEFAULT_EVENTS_MAX_BATCH_EVENTS,
    ) -> None:
        self._buffers: OrderedDict[
            str, list[BatchEvent]
        ] = OrderedDict()
        self._per_agent_cap = per_agent_cap
        self._wake: asyncio.Event = asyncio.Event()
        self._drops: dict[str, tuple[int, datetime]] = {}
        self._is_shutdown = False

    @property
    def is_shutdown(self) -> bool:
        return self._is_shutdown

    def push(self, address: str, events: list[BatchEvent]) -> bool:
        """Buffer events for an agent, dropping overflow.

        Returns ``False`` if the buffer has been shut down.
        """
        if not events:
            return True

        if self._is_shutdown:
            return False

        buffer = self._buffers.setdefault(address, [])
        remaining = self._per_agent_cap - len(buffer)

        if remaining > 0:
            if remaining >= len(events):
                buffer.extend(events)
            else:
                buffer.extend(events[:remaining])
                self._record_drop(address, len(events) - remaining)
            self._wake.set()
        else:
            self._record_drop(address, len(events))

        return True

    async def pop(
        self,
        max_events: int,
        timeout: float = 1.0,
    ) -> tuple[str, list[BatchEvent]] | None:
        """Take up to *max_events* from the next agent.

        Blocks until events are available.  Returns ``None`` only when
        the buffer has been shut down and is empty (the caller's signal
        to exit).

        During shutdown, returns remaining events without waiting so
        the consumer can drain the buffer.  The served agent is rotated
        to the back of the queue.
        """
        while not self._buffers:
            if self._is_shutdown:
                return None
            self._wake.clear()
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._wake.wait(), timeout=timeout)

        address, events = self._buffers.popitem(last=False)
        drops = self._drops.pop(address, None)

        event_limit = max_events - 1 if drops is not None else max_events

        if len(events) > event_limit:
            self._buffers[address] = events[event_limit:]
            events = events[:event_limit]

        if drops is not None:
            count, first_drop_at = drops
            events.append(
                BatchEvent(
                    category="user",
                    kind="info",
                    timestamp=first_drop_at,
                    message=(
                        f"{count} event(s) dropped due to full "
                        f"buffer (resumed at {_utc_now().isoformat()})"
                    ),
                    metadata={
                        "dropped_count": count,
                        "reason": "buffer_full",
                    },
                )
            )

        return address, events

    def shutdown(self) -> None:
        """Stop accepting new events and unblock any waiting ``pop()``."""
        self._is_shutdown = True
        self._wake.set()

    def _record_drop(self, address: str, count: int) -> None:
        prev_count, first_at = self._drops.get(address, (0, _utc_now()))
        self._drops[address] = (prev_count + count, first_at)


def _build_message_event(
    direction: MessageDirection,
    peer: str,
    session_id: UUID | None = None,
) -> BatchEvent:
    """Build a single message event."""
    metadata = MessageEventMetadata(
        direction=direction,
        peer=peer,
        msg_id=uuid4(),
        session_id=session_id,
    )
    verb = "received from" if direction == "received" else "sent to"
    return BatchEvent(
        category="user",
        kind="message",
        timestamp=_utc_now(),
        message=f"Message {verb} {peer}",
        metadata=metadata.model_dump(mode="json"),
    )


def _build_error_event(
    exception: Exception,
    traceback: str,
    category: EventCategory = "user",
) -> BatchEvent:
    """Build a single error event."""
    return BatchEvent(
        category=category,
        kind="error",
        timestamp=_utc_now(),
        exception=exception.__class__.__qualname__,
        traceback=traceback,
        message=str(exception),
    )


class EventsDispatcher:
    """Per-agent event dispatcher that buffers and POSTs telemetry
    events to the Agentverse events API.

    Provides a background worker (``start``/``stop``) for autonomous
    operation and a public ``post`` method for ``SharedEventsDispatcher``.
    """

    def __init__(
        self,
        identity: Identity,
        agentverse: AgentverseConfig,
        *,
        options: EventIngestionOptions | None = None,
        logger: logging.Logger | None = None,
        platform: PlatformMetadata | None = None,
    ) -> None:
        self._identity = identity
        self._agentverse = agentverse
        self._options = options or EventIngestionOptions()
        self._logger = logger
        self._platform = platform or PLATFORM_METADATA
        self._queue: asyncio.Queue[BatchEvent] = asyncio.Queue(
            maxsize=self._options.max_batch_events,
        )
        self._dropped_events_count = 0
        self._first_drop_at: datetime | None = None
        self._client: httpx.AsyncClient | None = None
        self._transport: RetryTransport | None = None
        self._worker_task: asyncio.Task[None] | None = None
        self._stopping = False

    @property
    def address(self) -> str:
        return self._identity.address


    def report_message(
        self,
        direction: MessageDirection,
        peer: str,
        session_id: UUID | None = None,
    ) -> None:
        """Enqueue a message event for a received or sent message."""
        try:
            event = _build_message_event(direction, peer, session_id)
        except Exception as exc:  # noqa: BLE001 - telemetry must never raise
            self._log(logging.DEBUG, f"Failed to build message event: {exc}")
            return
        self.enqueue([event])

    def report_exception(
        self,
        exception: Exception,
        traceback: str,
        category: EventCategory = "user",
    ) -> None:
        """Enqueue an error event for a handler or agent failure."""
        try:
            event = _build_error_event(exception, traceback, category)
        except Exception as exc:  # noqa: BLE001 - telemetry must never raise
            self._log(logging.DEBUG, f"Failed to build error event: {exc}")
            return
        self.enqueue([event])

    async def _post(self, events: list[BatchEvent]) -> None:
        """POST events to the Agentverse events API with attestation."""
        if self._transport is None:
            self._log(logging.DEBUG, "_post() called before transport is ready")
            return
        batch = AgentBatchEvents(platform=self._platform, events=events)
        try:
            await self._transport.post(
                self._agentverse.events_api,
                content=batch.model_dump_json(),
                headers=_auth_header(self._identity),
            )
        except httpx.HTTPStatusError as exc:
            self._log(
                logging.ERROR,
                f"Events batch rejected ({exc.response.status_code}): {exc}",
            )
            await self._report_system_error(
                f"Events batch rejected ({exc.response.status_code}): {exc}",
            )
        except Exception as exc:  # noqa: BLE001 - telemetry must never crash
            self._log(logging.ERROR, f"Events POST failed: {exc}")

    # -- Standalone lifecycle (not called when under Bureau) --

    async def start(self) -> None:
        """Start the background worker."""
        if self._worker_task is not None:
            return
        self._stopping = False
        self._client = httpx.AsyncClient(timeout=DEFAULT_EVENTS_HTTP_TIMEOUT_S)
        self._transport = RetryTransport(
            client=self._client,
            max_attempts=None,
            base_delay_s=self._options.retry_base_delay_s,
            max_delay_s=self._options.max_retry_delay_s,
            logger=self._logger,
        )
        self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self, *, drain_timeout: float | None = None) -> None:
        """Stop the background worker and close the HTTP client."""
        if self._worker_task is None:
            return
        drain_timeout = drain_timeout or self._options.shutdown_drain_timeout_s
        self._stopping = True

        try:
            self._queue.put_nowait(None)  # sentinel to unblock _take_next_batch
        except asyncio.QueueFull:
            pass  # worker will see _stopping on the next iteration

        with contextlib.suppress(asyncio.TimeoutError, asyncio.CancelledError):
            await asyncio.wait_for(self._worker_task, timeout=drain_timeout)

        self._worker_task = None
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._transport = None

    def _log(self, level: int, message: str) -> None:
        if self._logger is not None:
            self._logger.log(level, message)

    def enqueue(self, events: list[BatchEvent]) -> None:
        """Buffer events for dispatch."""
        if not events:
            return

        if self._stopping:
            self._log(
                logging.DEBUG,
                f"Events dropped during shutdown ({len(events)} events)",
            )
            return

        for event in events:
            try:
                self._queue.put_nowait(event)
            except asyncio.QueueFull:
                if self._first_drop_at is None:
                    self._first_drop_at = _utc_now()
                self._dropped_events_count += 1
                self._log(
                    logging.ERROR,
                    f"Events queue full; dropped event ({self._dropped_events_count} total)",
                )

    async def _worker_loop(self) -> None:
        while True:
            events = await self._take_next_batch()
            if events is None:
                if self._stopping:
                    return
                continue
            await self._post(events)

    async def _take_next_batch(self) -> list[BatchEvent] | None:
        events: list[BatchEvent] = []

        if self._dropped_events_count > 0:
            events.append(
                BatchEvent(
                    category="user",
                    kind="info",
                    timestamp=self._first_drop_at or _utc_now(),
                    message=(
                        f"{self._dropped_events_count} event(s) dropped due to full queue"
                        f" (resumed at {_utc_now().isoformat()})"
                    ),
                    metadata={
                        "dropped_count": self._dropped_events_count,
                        "reason": "queue_full",
                    },
                )
            )
            self._dropped_events_count = 0
            self._first_drop_at = None

        flush_time = _utc_now() + timedelta(seconds=self._options.flush_interval_s)

        while len(events) < self._options.max_batch_events and _utc_now() < flush_time:
            if not self._queue.empty():
                item = self._queue.get_nowait()
                if item is None:
                    break
                events.append(item)
                continue
            if self._stopping:
                break
            try:
                item = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=(flush_time - _utc_now()).total_seconds(),
                )
            except (asyncio.TimeoutError, asyncio.CancelledError):
                break
            if item is None:
                break
            events.append(item)

        if not events:
            return None
        return events

    async def _report_system_error(self, message: str) -> None:
        """Notify the platform that something failed on its side."""
        if self._transport is None:
            return
        try:
            error_batch = AgentBatchEvents.from_message(
                message, category="system", kind="error"
            )
            await self._transport.post(
                self._agentverse.events_api,
                content=error_batch.model_dump_json(),
                headers=_auth_header(self._identity),
            )
        except Exception as exc:  # noqa: BLE001 - telemetry must never raise
            self._log(logging.ERROR, f"Failed to report system error: {exc}")


class AgentEventsHandle:
    """Lightweight event handle for agents managed by a ``SharedEventsDispatcher``.

    Routes ``report_message`` and ``report_exception`` calls through
    a shared ``FairEventBuffer`` so a single background worker can
    dispatch events fairly across agents.

    Created by ``SharedEventsDispatcher.add_agent()`` — callers should
    not instantiate this directly.
    """

    def __init__(
        self,
        dispatcher: "EventsDispatcher",
        buffer: FairEventBuffer,
    ) -> None:
        self._dispatcher = dispatcher
        self._buffer = buffer

    @property
    def address(self) -> str:
        return self._dispatcher.address

    def report_message(
        self,
        direction: MessageDirection,
        peer: str,
        session_id: UUID | None = None,
    ) -> None:
        """Build a message event and push it to the shared buffer."""
        try:
            event = _build_message_event(direction, peer, session_id)
        except Exception:  # noqa: BLE001 - telemetry must never raise
            return
        self.enqueue([event])

    def report_exception(
        self,
        exception: Exception,
        traceback: str,
        category: EventCategory = "user",
    ) -> None:
        """Build an error event and push it to the shared buffer."""
        try:
            event = _build_error_event(exception, traceback, category)
        except Exception:  # noqa: BLE001 - telemetry must never raise
            return
        self.enqueue([event])

    def enqueue(self, events: list[BatchEvent]) -> None:
        """Push pre-built events to the shared buffer."""
        if events and not self._buffer.push(self._dispatcher.address, events):
            self._dispatcher._log(
                logging.DEBUG,
                f"Events dropped during shutdown ({len(events)} events)",
            )



class SharedEventsDispatcher:
    """Bureau-level coordinator with fair queuing across agents.

    Owns a single ``FairEventBuffer`` and one background worker.
    Each agent registers via ``add_agent()`` which returns an
    ``AgentEventsHandle``.  The worker pops events fairly and
    delegates the HTTP POST to the agent's own ``EventsDispatcher``.
    """

    def __init__(
        self,
        agentverse: AgentverseConfig,
        *,
        options: EventIngestionOptions | None = None,
        logger: logging.Logger | None = None,
        platform: PlatformMetadata | None = None,
    ) -> None:
        self._agentverse = agentverse
        self._options = options or EventIngestionOptions()
        self._logger = logger
        self._platform = platform or PLATFORM_METADATA
        self._buffer = FairEventBuffer(
            per_agent_cap=self._options.max_batch_events,
        )
        self._dispatchers: dict[str, EventsDispatcher] = {}
        self._client = httpx.AsyncClient(timeout=DEFAULT_EVENTS_HTTP_TIMEOUT_S)
        self._transport = RetryTransport(
            client=self._client,
            max_attempts=None,
            base_delay_s=self._options.retry_base_delay_s,
            max_delay_s=self._options.max_retry_delay_s,
            logger=self._logger,
        )
    def add_agent(self, dispatcher: EventsDispatcher) -> AgentEventsHandle:
        """Register an agent's dispatcher and return a push handle."""
        dispatcher._transport = self._transport
        self._dispatchers[dispatcher.address] = dispatcher
        return AgentEventsHandle(dispatcher, self._buffer)

    async def run(self) -> None:
        """Run the dispatch loop until ``stop()`` is called.

        Intended to be scheduled by the caller via ``create_task``.
        """
        try:
            while True:
                result = await self._buffer.pop(
                    self._options.max_batch_events,
                    timeout=self._options.flush_interval_s,
                )
                if result is None:
                    return
                address, events = result
                dispatcher = self._dispatchers.get(address)
                if dispatcher is not None:
                    await dispatcher._post(events)
        except asyncio.CancelledError:
            pass
        finally:
            if self._client is not None:
                await self._client.aclose()
                self._client = None
            self._transport = None

    def stop(self) -> None:
        """Signal the dispatch loop to drain and exit."""
        self._buffer.shutdown()

    def _log(self, level: int, message: str) -> None:
        if self._logger is not None:
            self._logger.log(level, message)
