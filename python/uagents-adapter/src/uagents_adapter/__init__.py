"""Adapters for uAgents to integrate with LangChain, CrewAI, and MCP."""

from importlib import metadata

from .a2a_outbound import A2AAgentConfig, MultiA2AAdapter, SingleA2AAdapter, a2a_servers
from .a2a_inbound import A2ARegisterTool
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
    "A2ARegisterTool",
    "LangchainRegisterTool",
    "CrewaiRegisterTool",
    "MCPServerAdapter",
    "ResponseMessage",
    "A2AAgentConfig",
    "MultiA2AAdapter",
    "a2a_servers",
    "SingleA2AAdapter",
    "cleanup_uagent",
    "cleanup_all_uagents",
    "__version__",
]
