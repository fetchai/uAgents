"""Adapters for uAgents to integrate with LangChain and CrewAI."""

from importlib import metadata

from .common import ResponseMessage, cleanup_all_uagents, cleanup_uagent
from .crewai import CrewaiRegisterTool
from .langchain import LangchainRegisterTool

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


__all__ = [
    "LangchainRegisterTool",
    "CrewaiRegisterTool",
    "ResponseMessage",
    "cleanup_uagent",
    "cleanup_all_uagents",
    "__version__",
]
