"""LangChain integration for registering agents on Agentverse."""

from importlib import metadata

from .agent_utils import AgentManager
from .tools import LangchainRegisterTool, QueryMessage

try:
    __version__ = metadata.version(__package__.split(".")[0])
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


__all__ = [
    "LangchainRegisterTool",
    "QueryMessage",
    "__version__",
    "AgentManager",
]
