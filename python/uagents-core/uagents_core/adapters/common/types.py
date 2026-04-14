import platform
from datetime import datetime
from functools import cached_property
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Literal
from urllib.parse import unquote, urlparse
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from uagents_core.adapters.common.helpers import utc_now
from uagents_core.config import AgentverseConfig
from uagents_core.identity import Identity
from uagents_core.registration import AgentProfile

try:
    sdk_version = version("uagents-core")
except PackageNotFoundError:
    sdk_version = "0.0.0"


class AgentUri(BaseModel):
    key: str
    name: str
    agentverse: AgentverseConfig
    handle: str | None = None

    model_config = ConfigDict(frozen=True)

    @cached_property
    def identity(self) -> Identity:
        return Identity.from_seed(self.key, 0)

    @classmethod
    def from_str(cls, uri: str) -> "AgentUri":
        parsed = urlparse(uri)

        if not parsed.scheme:
            raise ValueError("Scheme is missing.")
        if not parsed.hostname:
            raise ValueError("Hostname is missing.")
        if not parsed.username:
            raise ValueError("Agent handle is missing")
        if not parsed.password:
            raise ValueError("Agent key is missing.")
        if not parsed.path or len(parsed.path.split("/")) < 2:
            raise ValueError("Agent name is missing")

        name = unquote(parsed.path.split("/")[1])

        agentverse = AgentverseConfig(
            base_url=parsed.hostname + (f":{parsed.port}" if parsed.port else ""),
            http_prefix=parsed.scheme,
        )

        return cls(
            key=parsed.password,
            name=name,
            agentverse=agentverse,
            handle=parsed.username,
        )


# TODO
class AgentOptions(BaseModel):
    verify_envelope: bool = True


class AgentverseAgent(BaseModel):
    uri: AgentUri
    profile: AgentProfile | None = None
    metadata: dict[str, Any] | None = None
    options: AgentOptions = AgentOptions()


class AgentStarletteState(BaseModel):
    key: str
    agentverse: AgentverseConfig

    model_config = ConfigDict(frozen=True)

    @cached_property
    def identity(self) -> Identity:
        return Identity.from_seed(self.key, 0)


EventCategory = Literal["system", "user"]
EventKind = Literal["error", "interaction", "info"]


class OperatingSystemMetadata(BaseModel):
    name: str = Field(description="Operating system name (e.g. Linux, Darwin)")
    version: str = Field(description="Operating system version string")
    release: str = Field(description="Operating system release string")


class PlatformMetadata(BaseModel):
    operating_system: OperatingSystemMetadata = Field(
        description="Nested operating system details"
    )
    python_version: str = Field(description="Python interpreter version")
    processor: str = Field(description="Processor architecture identifier")
    nodename: str = Field(description="Network hostname of the machine")
    sdk_version: str = Field(description="uagents-core SDK version")

    @classmethod
    def current(cls) -> "PlatformMetadata":
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


class BatchEvent(BaseModel):
    """A single event within a batch. Fields that are constant across the
    batch (agent_address, platform) live on AgentEvents instead."""

    id: UUID = Field(
        default_factory=uuid4,
        description="Client-assigned UUIDv4 identifier for idempotent ingestion",
    )
    category: EventCategory = Field(description="Top-level event category")
    kind: EventKind = Field(description="Specific event kind within the category")
    timestamp: datetime = Field(description="UTC timestamp when the event occurred")
    exception: str | None = Field(
        default=None,
        description="Qualified class name of the exception, if this is an error event",
    )
    traceback: str | None = Field(
        default=None,
        description="Full traceback string for error events",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary key-value metadata attached by the agent",
    )
    message: str | None = Field(
        default=None,
        description="Human-readable event message",
    )


class AgentBatchEvents(BaseModel):
    """A batch of events from a single agent. The platform
    metadata are shared across all events in the batch."""

    platform: PlatformMetadata = Field(
        description="Platform metadata at the time the events were produced",
    )
    events: list[BatchEvent] = Field(description="Individual events in the batch")

    @classmethod
    def from_exception(cls, exception: Exception, traceback: str) -> "AgentBatchEvents":
        return cls(
            platform=PLATFORM_METADATA,
            events=[
                BatchEvent(
                    category="system",
                    kind="error",
                    timestamp=utc_now(),
                    exception=exception.__class__.__qualname__,
                    traceback=traceback,
                    metadata=None,
                    message=str(exception),
                )
            ],
        )

    @classmethod
    def from_message(
        cls,
        message: str,
        category: EventCategory = "user",
        kind: EventKind = "info",
    ) -> "AgentBatchEvents":
        return cls(
            platform=PLATFORM_METADATA,
            events=[
                BatchEvent(
                    category=category,
                    kind=kind,
                    timestamp=utc_now(),
                    message=message,
                )
            ],
        )


class SingleEvent(BatchEvent):
    """An individual event, with agent address and platform metadata included
    for convenience."""

    agent_address: str = Field(
        max_length=66,
        description="Agent address in the format agent1q...",
    )
    platform: PlatformMetadata = Field(
        description="Platform metadata at the time the event was produced",
    )
