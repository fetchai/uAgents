"""uAgent A2A Adapter Package for A2A Integration."""

from importlib import metadata

from .adapter import A2AAgentConfig, MultiA2AAdapter, SingleA2AAdapter, a2a_servers

try:
    __version__ = metadata.version(__package__.split(".")[0])
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


__all__ = [
    "A2AAgentConfig",
    "SingleA2AAdapter",
    "MultiA2AAdapter",
    "a2a_servers",
    "__version__",
]
