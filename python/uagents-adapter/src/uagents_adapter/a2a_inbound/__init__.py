"""A2A Inbound Adapter - Allows A2A agents to communicate with uAgents/Agentverse."""

from importlib import metadata

from .adapter import A2ARegisterTool

try:
    __version__ = metadata.version(__package__.split(".")[0])
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


__all__ = [
    "A2ARegisterTool",
    "__version__",
]
