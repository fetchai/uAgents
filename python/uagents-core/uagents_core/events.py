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
        sdk_version: str = DEFAULT_SDK_VERSION,
        category: EventCategory = "user",
        kind: EventKind = "info",
        metadata: dict[str, Any] | None = None,
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
        sdk_version: str = DEFAULT_SDK_VERSION,
        category: EventCategory = "system",
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


def _is_client_error(error: httpx.HTTPStatusError) -> bool:
    """
    Return True for 4xx errors that indicate a bad payload (so we stop retrying).

    401 is excluded because it's an auth issue that may resolve on the next
    attempt when a fresh attestation token is generated.
    """
    code = error.response.status_code
    return 400 <= code < 500 and code != 401


class _BaseEventsDispatcher:
    """
    Shared background buffer that POSTs telemetry to the Agentverse events API.

    The queue stores ``(identity, batch)`` pairs so one dispatcher can serve many
    agents as in the ``Bureau``: each item is signed with the identity that
    was supplied at enqueue time. Events from different identities are never
    merged into the same HTTP POST, because ``POST /v1/events`` is attested as
    a single agent.

    Adapted from the ``agentverse-sdk`` events dispatcher
    (https://github.com/fetchai/agentverse-core/pull/6139).
    """

    def __init__(
        self,
        agentverse: AgentverseConfig,
        options: EventIngestionOptions | None = None,
        *,
        logger: logging.Logger | None = None,
        platform: PlatformMetadata | None = None,
    ) -> None:
        self._agentverse = agentverse
        self._options = options or EventIngestionOptions()
        self._logger = logger
        self._platform = platform or PLATFORM_METADATA
        self._queue: asyncio.Queue[tuple[Identity, AgentBatchEvents]] = asyncio.Queue(
            maxsize=self._options.queue_max_batches
        )
        # Item taken from the queue that belonged to a different identity than
        # the batch currently being built; flushed on the next pass.
        self._pending: tuple[Identity, AgentBatchEvents] | None = None
        self._client: httpx.AsyncClient | None = None
        self._worker_task: asyncio.Task[None] | None = None
        self._stopping = False
        self._dropped_events_count = 0
        self._first_drop_at: datetime | None = None

    @property
    def events_url(self) -> str:
        return self._agentverse.events_api

    def _log(self, level: int, message: str) -> None:
        if self._logger is not None:
            self._logger.log(level, message)

    def _enqueue(self, identity: Identity, batch: AgentBatchEvents) -> None:
        """Queue a batch to be POSTed with an attestation for ``identity``."""
        if not batch.events:
            return
        if self._stopping:
            self._log(
                logging.DEBUG,
                f"Events dropped during shutdown ({len(batch.events)} events)",
            )
            return
        try:
            self._queue.put_nowait((identity, batch))
        except asyncio.QueueFull:
            if self._first_drop_at is None:
                self._first_drop_at = _utc_now()
            self._dropped_events_count += len(batch.events)
            self._log(
                logging.ERROR,
                f"Events queue full; dropped newest batch ({len(batch.events)} events)",
            )

    async def start(self) -> None:
        if self._worker_task is not None:
            return
        self._stopping = False
        self._client = httpx.AsyncClient(timeout=DEFAULT_EVENTS_HTTP_TIMEOUT_S)
        self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self, *, drain_timeout: float | None = None) -> None:
        if self._worker_task is None:
            return
        drain_timeout = drain_timeout or self._options.shutdown_drain_timeout_s
        self._stopping = True
        # ``wait_for`` cancels the worker if the drain exceeds the timeout.
        with contextlib.suppress(TimeoutError, asyncio.CancelledError):
            await asyncio.wait_for(self._worker_task, timeout=drain_timeout)
        self._worker_task = None
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _worker_loop(self) -> None:
        while True:
            item = await self._take_next_batch()
            if item is None:
                if self._stopping and self._pending is None and self._queue.empty():
                    return
                continue
            identity, batch = item
            await self._post_batch(identity, batch)

    async def _post(self, identity: Identity, data: AgentBatchEvents) -> None:
        assert self._client is not None
        response = await self._client.post(
            self.events_url,
            content=data.model_dump_json(),
            headers=_auth_header(identity),
        )
        response.raise_for_status()

    async def _post_batch(self, identity: Identity, batch: AgentBatchEvents) -> None:
        attempts = 0
        while True:
            try:
                await self._post(identity, batch)
                return
            except Exception as exc:  # noqa: BLE001 - retried/logged below
                if isinstance(exc, httpx.HTTPStatusError) and _is_client_error(exc):
                    self._log(
                        logging.ERROR,
                        f"Events batch rejected by server "
                        f"({exc.response.status_code}), skipping: {exc}",
                    )
                    await self._report_system_error(
                        identity,
                        f"Events batch rejected by server "
                        f"({exc.response.status_code}): {exc}",
                    )
                    return
                self._log(logging.ERROR, f"Events dispatcher POST failed: {exc}")
                delay = min(
                    self._options.retry_base_delay_s * (2**attempts),
                    self._options.max_retry_delay_s,
                )
                attempts += 1
                await asyncio.sleep(delay)

    async def _report_system_error(self, identity: Identity, message: str) -> None:
        """Report an SDK error directly to the events API, bypassing the queue."""
        try:
            await self._post(
                identity,
                AgentBatchEvents.from_message(message, category="system", kind="error"),
            )
        except Exception as exc:  # noqa: BLE001 - telemetry must never raise
            self._log(logging.ERROR, f"Failed to report system error: {exc}")

    async def _take_next_batch(
        self,
    ) -> tuple[Identity, AgentBatchEvents] | None:
        """
        Pull the next flushable batch for a single identity.

        Coalesces consecutive queue items that share the same agent address.
        Items for a different identity are held in ``_pending`` for the next pass.
        """
        if self._pending is not None:
            identity, first = self._pending
            self._pending = None
        elif not self._queue.empty():
            identity, first = self._queue.get_nowait()
        elif self._stopping:
            return None
        else:
            try:
                identity, first = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=self._options.flush_interval_s,
                )
            except (TimeoutError, asyncio.CancelledError):
                return None

        events: list[BatchEvent] = list(first.events)

        if self._dropped_events_count > 0:
            events.insert(
                0,
                BatchEvent(
                    category="user",
                    kind="info",
                    timestamp=self._first_drop_at or _utc_now(),
                    message=(
                        f"{self._dropped_events_count} event(s) dropped due to full "
                        f"queue (resumed at {_utc_now().isoformat()})"
                    ),
                    metadata={
                        "dropped_count": self._dropped_events_count,
                        "reason": "queue_full",
                    },
                ),
            )
            self._dropped_events_count = 0
            self._first_drop_at = None

        flush_time = _utc_now() + timedelta(seconds=self._options.flush_interval_s)

        while len(events) < self._options.max_batch_events and _utc_now() < flush_time:
            if self._pending is not None:
                break
            if not self._queue.empty():
                next_identity, next_batch = self._queue.get_nowait()
                if next_identity.address != identity.address:
                    self._pending = (next_identity, next_batch)
                    break
                events.extend(next_batch.events)
                continue
            if self._stopping:
                break
            try:
                next_identity, next_batch = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=(flush_time - _utc_now()).total_seconds(),
                )
            except (TimeoutError, asyncio.CancelledError):
                break
            if next_identity.address != identity.address:
                self._pending = (next_identity, next_batch)
                break
            events.extend(next_batch.events)

        if not events:
            return None

        return identity, AgentBatchEvents(platform=self._platform, events=events)


class EventsDispatcher(_BaseEventsDispatcher):
    """
    Identity-bound events dispatcher for a single agent.

    Used by the native uAgents ``Agent`` runtime: callers do not pass an identity
    on each enqueue because it was fixed in the constructor.
    """

    def __init__(
        self,
        identity: Identity,
        agentverse: AgentverseConfig,
        options: EventIngestionOptions | None = None,
        *,
        logger: logging.Logger | None = None,
        platform: PlatformMetadata | None = None,
    ) -> None:
        super().__init__(agentverse, options, logger=logger, platform=platform)
        self._identity = identity

    def enqueue_event(self, batch: AgentBatchEvents) -> None:
        """Enqueue a batch signed as this dispatcher's agent."""
        self._enqueue(self._identity, batch)

    def report_message(
        self,
        direction: MessageDirection,
        peer: str,
        session_id: UUID | None = None,
    ) -> None:
        """Enqueue a ``message`` event for a received or sent message."""
        try:
            metadata = MessageEventMetadata(
                direction=direction,
                peer=peer,
                msg_id=uuid4(),
                session_id=session_id,
            )
            verb = "received from" if direction == "received" else "sent to"
            batch = AgentBatchEvents.from_message(
                f"Message {verb} {peer}",
                category="user",
                kind="message",
                metadata=metadata.model_dump(mode="json"),
            )
        except Exception as exc:  # noqa: BLE001 - telemetry must never raise
            self._log(logging.DEBUG, f"Failed to build message event: {exc}")
            return
        self.enqueue_event(batch)

    def report_exception(
        self,
        exception: Exception,
        traceback: str,
        category: EventCategory = "user",
    ) -> None:
        """Enqueue an ``error`` event for a handler/agent failure."""
        try:
            batch = AgentBatchEvents.from_exception(
                exception, traceback, category=category
            )
        except Exception as exc:  # noqa: BLE001 - telemetry must never raise
            self._log(logging.DEBUG, f"Failed to build error event: {exc}")
            return
        self.enqueue_event(batch)


class MultiAgentEventsDispatcher(_BaseEventsDispatcher):
    """
    One dispatcher shared across many agents.

    Callers pass the executing agent's identity on every enqueue so each POST
    is attested as that agent.
    """

    def enqueue_event(self, identity: Identity, batch: AgentBatchEvents) -> None:
        """Enqueue a batch signed as ``identity``."""
        self._enqueue(identity, batch)
