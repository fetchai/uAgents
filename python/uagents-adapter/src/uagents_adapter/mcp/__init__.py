"""MCP (Model Control Protocol) integration for uAgents."""

from importlib import metadata

from .adapter import MCPServerAdapter
from .protocol import CallTool, CallToolResponse, ListTools, ListToolsResponse

try:
    __version__ = metadata.version(__package__.split(".")[0])
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


__all__ = [
    "MCPServerAdapter",
    "ListTools",
    "ListToolsResponse",
    "CallTool",
    "CallToolResponse",
    "__version__",
]
