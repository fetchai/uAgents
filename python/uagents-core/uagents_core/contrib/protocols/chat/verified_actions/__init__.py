"""
Verified Actions schemas and MetadataContent helpers.

Verified Actions data is carried in ``MetadataContent`` blocks; the chat
protocol digest is unchanged.  Use ``create_verified_actions_content()`` to
emit blocks and ``extract_verified_actions()`` to read them.

The types defined here serve as the **contract** for verified actions data
carried inside ``ChatMessage`` metadata blocks.

Wire format: ``MetadataContent.metadata`` is ``dict[str, str]``.
``verified_actions_data`` is a JSON-stringified :class:`VerifiedActions`.
"""

import logging
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from uagents_core.contrib.protocols.chat import MetadataContent

_logger = logging.getLogger(__name__)

VERIFIED_ACTIONS_VERSION = "1"

META_VERIFIED_ACTIONS_VERSION = "verified_actions_version"
META_VERIFIED_ACTIONS_DATA = "verified_actions_data"


# ── Base with shared fields ──────────────────────────────────────────────


class _ToolActionBase(BaseModel):
    """Common fields for all tool action types."""

    model_config = ConfigDict(extra="ignore")

    reference_id: str = Field(
        description="UUID4 linking this action to its AEVS receipt",
    )
    status: str = Field(
        description="Outcome of the action: 'success' or 'error'",
    )
    error: str | None = Field(
        default=None,
        description="Error message when status is 'error'",
    )
    duration_ms: int = Field(
        description="Wall-clock duration of the action in milliseconds",
    )


# ── Concrete tool action types ───────────────────────────────────────────


class WebAction(_ToolActionBase):
    """An outbound HTTP call captured by the platform."""

    type: Literal["web"] = "web"
    url: str
    method: str
    status_code: int | None = None


class LlmAction(_ToolActionBase):
    """A call to a large language model API."""

    type: Literal["llm"] = "llm"
    api_url: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class McpAction(_ToolActionBase):
    """A tool invocation via the Model Context Protocol."""

    type: Literal["mcp"] = "mcp"
    server_url: str
    tool_name: str


class IntegrationAction(_ToolActionBase):
    """A tool execution via a managed platform integration."""

    type: Literal["integration"] = "integration"
    integration: str
    tool_name: str


# ── Discriminated union ──────────────────────────────────────────────────

ToolAction = Annotated[
    WebAction | LlmAction | McpAction | IntegrationAction,
    Field(discriminator="type"),
]


# ── Aggregate ────────────────────────────────────────────────────────────


class VerifiedActions(BaseModel):
    """All tool actions captured during a single agent execution."""

    model_config = ConfigDict(extra="ignore")

    session_id: str = Field(
        description="UUID4 identifying the agent execution session",
    )
    actions: list[ToolAction] = Field(
        description="Ordered list of captured tool actions",
    )


# ── MetadataContent helpers ───────────────────────────────────────────────


def create_verified_actions_content(
    data: VerifiedActions,
) -> MetadataContent:
    """Build a Verified Actions block as ``MetadataContent`` for ``ChatMessage``."""
    metadata: dict[str, str] = {
        META_VERIFIED_ACTIONS_VERSION: VERIFIED_ACTIONS_VERSION,
        META_VERIFIED_ACTIONS_DATA: data.model_dump_json(exclude_none=True),
    }
    return MetadataContent(metadata=metadata)


def extract_verified_actions(
    content: MetadataContent,
) -> VerifiedActions | None:
    """Return validated ``VerifiedActions``, or ``None`` if not a match.

    Attempts to parse any version — unknown fields from newer versions are
    silently ignored.  Consumers can compare ``VERIFIED_ACTIONS_VERSION``
    against ``content.metadata[META_VERIFIED_ACTIONS_VERSION]`` to detect
    outdated producers and prompt them to upgrade.
    """
    metadata = content.metadata
    if META_VERIFIED_ACTIONS_VERSION not in metadata:
        return None

    raw = metadata.get(META_VERIFIED_ACTIONS_DATA)
    if raw is None:
        _logger.warning("verified actions metadata missing data payload")
        return None

    try:
        return VerifiedActions.model_validate_json(raw)
    except ValidationError:
        _logger.warning("verified actions data failed validation", exc_info=True)
        return None


def validate_tool_action(raw: dict) -> ToolAction | None:
    """Validate a raw dict (e.g. from the VM queue) as a typed ``ToolAction``.

    Returns ``None`` on validation failure — never raises.
    """
    try:
        return TypeAdapter(ToolAction).validate_python(raw)
    except ValidationError:
        _logger.warning("tool action dict failed validation", exc_info=True)
        return None
