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
    # Do not define placeholders; raise a clear ImportError on access instead

try:
    from composio.types import Tool, ToolExecuteParams, ToolExecutionResponse

    from .composio import (
        AfterExecute,
        AuthConfigId,
        AuthenticationError,
        AuthResponse,
        BeforeExecute,
        ComposioConfig,
        ComposioError,
        ComposioService,
        ConfigurationError,
        ConnectionError,
        ConnectionStatus,
        Modifiers,
        PostgresMemoryConfig,
        SchemaModifier,
        SessionId,
        ToolConfig,
        ToolRetrievalError,
        ToolSlug,
        UserId,
    )
    COMPOSIO_AVAILABLE = True
except ImportError:
    COMPOSIO_AVAILABLE = False

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

if COMPOSIO_AVAILABLE:
    __all__.extend(
        [
            # Main classes
            "ComposioService",
            "ComposioConfig",
            "ToolConfig",
            "Modifiers",
            "PostgresMemoryConfig",
            # Response models
            "ConnectionStatus",
            "AuthResponse",
            # Exceptions
            "ComposioError",
            "AuthenticationError",
            "ConnectionError",
            "ConfigurationError",
            "ToolRetrievalError",
            # Type aliases
            "UserId",
            "AuthConfigId",
            "ToolSlug",
            "SessionId",
            # Tool types
            "Tool",
            "ToolExecuteParams",
            "ToolExecutionResponse",
            "SchemaModifier",
            "BeforeExecute",
            "AfterExecute",
        ]
    )
