"""LangChain integration for registering agents on Agentverse."""

from importlib import metadata

from .tools import (
    QueryMessage,
    ResponseMessage,
    UAgentRegisterTool,
    cleanup_all_uagents,
    cleanup_uagent,
)

try:
    __version__ = metadata.version(__package__.split(".")[0])
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


__all__ = [
    "UAgentRegisterTool",
    "QueryMessage",
    "ResponseMessage",
    "cleanup_uagent",
    "cleanup_all_uagents",
    "__version__",
]
