"""Adapters for uAgents to integrate with LangChain, CrewAI, and MCP."""

from importlib import metadata

from .common import ResponseMessage, cleanup_all_uagents, cleanup_uagent
from .crewai import CrewaiRegisterTool
from .langchain import LangchainRegisterTool
from .mcp import MCPServerAdapter

# Conditional imports for A2A modules
try:
    from .a2a_inbound import A2ARegisterTool
    from .a2a_outbound import (
        A2AAgentConfig,
        MultiA2AAdapter,
        SingleA2AAdapter,
        a2a_servers,
    )

    A2A_AVAILABLE = True
except ImportError:
    A2A_AVAILABLE = False
    # Create dummy classes for when A2A is not available
    A2ARegisterTool = None
    A2AAgentConfig = None
    MultiA2AAdapter = None
    SingleA2AAdapter = None
    a2a_servers = None

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


# Build __all__ list conditionally
__all__ = [
    "LangchainRegisterTool",
    "CrewaiRegisterTool",
    "MCPServerAdapter",
    "ResponseMessage",
    "cleanup_uagent",
    "cleanup_all_uagents",
    "__version__",
]

# Add A2A modules only if available
if A2A_AVAILABLE:
    __all__.extend(
        [
            "A2ARegisterTool",
            "A2AAgentConfig",
            "MultiA2AAdapter",
            "a2a_servers",
            "SingleA2AAdapter",
        ]
    )
