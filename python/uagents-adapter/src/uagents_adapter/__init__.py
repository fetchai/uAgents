"""Adapters for uAgents to integrate with LangChain, CrewAI, and MCP."""

from importlib import metadata

from .common import ResponseMessage, cleanup_all_uagents, cleanup_uagent
from .crewai import CrewaiRegisterTool
from .langchain import LangchainRegisterTool
from .mcp import MCPServerAdapter

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


__all__ = [
    "LangchainRegisterTool",
    "CrewaiRegisterTool",
    "MCPServerAdapter",
    "ResponseMessage",
    "cleanup_uagent",
    "cleanup_all_uagents",
    "__version__",
]
