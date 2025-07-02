"""Protocol definitions for MCP (Model Control Protocol)."""

from typing import Any

from uagents import Model
from uagents_core.protocol import ProtocolSpecification


class ListTools(Model):
    """Request to list available tools."""

    session_id: str | None = None  # Add session ID


class ListToolsResponse(Model):
    """Response containing available tools or error."""

    tools: list[dict[str, Any]] | None = None
    error: str | None = None


class CallTool(Model):
    """Request to call a specific tool with arguments."""

    request_id: str  # Unique request ID
    session_id: str | None = None  # Add session ID
    tool: str
    args: dict[str, Any]


class CallToolResponse(Model):
    """Response from a tool call containing result or error."""

    result: str | None = None
    error: str | None = None


class ResetTools(Model):
    """Request to reset tool state for a session or globally."""

    session_id: str | None = None  # Optional session ID for targeted reset


class ResetToolsResponse(Model):
    """Response indicating whether the reset was successful."""

    success: bool
    error: str | None = None


# Protocol specification for MCP
mcp_protocol_spec = ProtocolSpecification(
    name="MCPProtocol",
    version="0.2.0",  # Updated version
    interactions={
        ListTools: {ListToolsResponse},
        CallTool: {CallToolResponse},
        ResetTools: {ResetToolsResponse},
    },
    roles={"client": set(), "server": {ListTools, CallTool, ResetTools}},
)
