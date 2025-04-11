"""CrewAI integration for registering agents on Agentverse."""

from importlib import metadata

from .tools import (
    CrewAIRegisterTool,
    QueryMessage,
    ResponseMessage,
    cleanup_all_uagents,
    cleanup_uagent,
)

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)

__all__ = [
    "CrewAIRegisterTool",
    "QueryMessage",
    "ResponseMessage",
    "cleanup_uagent",
    "cleanup_all_uagents",
    "__version__",
]
