"""uAgent A2A Adapter Package for A2A Integration."""

from importlib import metadata

from .adapter import A2AAdapter, A2AAgentConfig

try:
    __version__ = metadata.version(__package__.split(".")[0])
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)


__all__ = [
    "A2AAdapter",
    "A2AAgentConfig",
    "__version__",
]
