"""Langchain integration for registering agents on Agentverse."""

from importlib import metadata

from .tools import (
    UAgentRegisterTool,
    QueryMessage,
    ResponseMessage,
    cleanup_uagent,
    cleanup_all_uagents,
)

try:
    __version__ = metadata.version(__package__)
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