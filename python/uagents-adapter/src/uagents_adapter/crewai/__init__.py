"""CrewAI integration for registering crews on Agentverse."""

from importlib import metadata

from .tools import CrewaiRegisterTool

try:
    __version__ = metadata.version(__package__.split(".")[0])
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


__all__ = [
    "CrewaiRegisterTool",
    "__version__",
]
