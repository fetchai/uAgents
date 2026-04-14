import contextlib
import json
import platform
import traceback
from datetime import datetime
from typing import Any, Literal

import requests
from pydantic import BaseModel
from requests import HTTPError
from uagents_core import __version__ as sdk_version
from uagents_core.adapters.common.agentverse import (
    _post_data,
    _post_data_sync,
    generate_agent_auth_token,
)
from uagents_core.adapters.common.config import DEFAULT_HTTP_REQUESTS_TIMEOUT
from uagents_core.adapters.common.helpers import utc_now
from uagents_core.adapters.common.logger import logger
from uagents_core.adapters.common.types import AgentUri

FAILED_INIT_ERROR_FORMAT = "Failed to initialize agentverse sdk ({})"

EventCategory = Literal["system", "user"]
EventKind = Literal["error", "interaction", "info"]


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


def get_agent_address(agent: str | AgentUri) -> str | None:
    if isinstance(agent, str):
        try:
            agent = AgentUri.from_str(agent)
        except Exception:
            return None

    return agent.identity.address


class Event(BaseModel):
    category: EventCategory
    kind: EventKind
    timestamp: datetime
    platform: PlatformMetadata
    agent_address: str
    exception: str | None
    traceback: str | None
    metadata: dict[str, Any] | None
    message: str | None

    @classmethod
    def from_exception(
        cls, uri: AgentUri, exception: Exception, traceback: str
    ) -> "Event":
        return cls(
            category="system",
            kind="error",
            timestamp=utc_now(),
            platform=PLATFORM_METADATA,
            agent_address=uri.identity.address,
            exception=exception.__class__.__qualname__,
            traceback=traceback,
            metadata=None,
            message=str(exception),
        )


def dispatch_event(uri: AgentUri, event: Event):
    _post_data_sync(
        url=f"{uri.agentverse.url}/v1/events",
        data=json.dumps([event.model_dump()]),
        headers={"Authorization": f"Agent {generate_agent_auth_token(uri.identity)}"},
    )


@contextlib.contextmanager
def handle_init_errors(uri: AgentUri):
    try:
        yield
    except Exception as e:
        event = Event.from_exception(uri, e, traceback.format_exc())
        try:
            dispatch_event(uri, event)
        except HTTPError as dispatch_exception:
            logger.error(
                FAILED_INIT_ERROR_FORMAT.format(dispatch_exception.response.status_code)
            )  # TODO(LR): make sure timestamps are included in logger formatting
        except Exception as generic_exception:
            logger.error(FAILED_INIT_ERROR_FORMAT.format(str(generic_exception)))
