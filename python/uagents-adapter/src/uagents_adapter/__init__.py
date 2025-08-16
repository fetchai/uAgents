"""Adapters for uAgents to integrate with LangChain, CrewAI, and MCP."""

from importlib import metadata

# Import common utilities (should always be available)
from .common import ResponseMessage, cleanup_all_uagents, cleanup_uagent

# Try to import optional adapters
try:
    from .crewai import CrewaiRegisterTool
    _CREWAI_AVAILABLE = True
except ImportError:
    CrewaiRegisterTool = None
    _CREWAI_AVAILABLE = False

try:
    from .langchain import LangchainRegisterTool
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    LangchainRegisterTool = None
    _LANGCHAIN_AVAILABLE = False

try:
    from .mcp import MCPServerAdapter
    _MCP_AVAILABLE = True
except ImportError:
    MCPServerAdapter = None
    _MCP_AVAILABLE = False

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


__all__ = [
    "ResponseMessage",
    "cleanup_uagent",
    "cleanup_all_uagents",
    "__version__",
]

# Add available adapters to __all__
if _LANGCHAIN_AVAILABLE:
    __all__.append("LangchainRegisterTool")
if _CREWAI_AVAILABLE:
    __all__.append("CrewaiRegisterTool")
if _MCP_AVAILABLE:
    __all__.append("MCPServerAdapter")
