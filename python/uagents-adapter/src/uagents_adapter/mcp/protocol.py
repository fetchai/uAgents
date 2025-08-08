"""Protocol definitions for MCP (Model Control Protocol)."""

from typing import Any, Dict, List, Optional

from uagents import Model
from uagents_core.protocol import ProtocolSpecification


class ListTools(Model):
    """Request to list available tools."""

    pass


class ListToolsResponse(Model):
    """Response containing available tools or error."""

    tools: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class CallTool(Model):
    """Request to call a specific tool with arguments."""

    tool: str
    args: Dict[str, Any]


class CallToolResponse(Model):
    """Response from a tool call containing result or error."""

    result: Optional[str] = None
    error: Optional[str] = None


# Protocol specification for MCP
mcp_protocol_spec = ProtocolSpecification(
    name="MCPProtocol",
    version="0.1.0",
    interactions={ListTools: {ListToolsResponse}, CallTool: {CallToolResponse}},
    roles={"client": set(), "server": {ListTools, CallTool}},
)
