"""
Telemetry events for Agentverse-registered agents.

This module defines the event schema understood by the Agentverse events API
(``POST {agentverse.url}/v1/events``) together with the helpers used to
authenticate against, dispatch events to, and query the registration status
from Agentverse.

The schema mirrors the one used by the ``agentverse-sdk`` adapters so that
events emitted by native uAgents render consistently in the Agentverse UI.

Telemetry must never interfere with agent logic: :func:`dispatch_events` and
:func:`is_registered_on_agentverse` swallow every error (failing closed) and
never raise into the caller.
"""

import logging
import platform
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version
from secrets import token_bytes
from typing import Any, Literal
from uuid import UUID, uuid4

import httpx
from pydantic import BaseModel, Field, model_validator

from uagents_core.config import AgentverseConfig
from uagents_core.identity import Identity
from uagents_core.storage import compute_attestation

EventCategory = Literal["system", "user"]
EventKind = Literal["error", "info", "message"]
MessageDirection = Literal["received", "sent"]

# Attestation tokens for telemetry requests are short-lived by design.
AUTH_TOKEN_VALIDITY_SECS = 120

# Path of the Agentverse events endpoint, relative to the Agentverse base url.
EVENTS_PATH = "/v1/events"


def _resolve_default_sdk_version() -> str:
    """
    Best-effort lookup of the version to report as ``sdk_version``.

    Prefers the ``uagents`` runtime version (the common consumer of this module),
    falling back to ``uagents-core`` and finally ``"unknown"``.
    """
    for package in ("uagents", "uagents-core"):
        try:
            return _package_version(package)
        except PackageNotFoundError:
            continue
    return "unknown"


# Resolved once at import time and used as the default for event metadata so
# callers (e.g. the uAgents runtime) don't need to compute or thread it through.
DEFAULT_SDK_VERSION = _resolve_default_sdk_version()


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
    timeout: int = 10,
) -> None:
    """
    POST a batch of events to the Agentverse events API.

    Failures are swallowed (and optionally logged at debug level): telemetry
    must never crash or interfere with the agent.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{agentverse.url}{EVENTS_PATH}",
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
