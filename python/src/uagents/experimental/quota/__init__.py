"""
Deprecated location for the QuotaProtocol.

`QuotaProtocol` and its helpers have moved to `uagents.protocol.quota`. This module
re-exports them for backwards compatibility and will be removed in a future release.
"""

import warnings

from uagents.protocol.quota import (
    MAX_REQUESTS,
    WINDOW_SIZE_MINUTES,
    AccessControlList,
    QuotaProtocol,
    RateLimit,
    Usage,
)

warnings.warn(
    "`uagents.experimental.quota` has moved to `uagents.protocol.quota`. "
    "Please update your imports; the experimental location will be removed "
    "in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "MAX_REQUESTS",
    "WINDOW_SIZE_MINUTES",
    "AccessControlList",
    "QuotaProtocol",
    "RateLimit",
    "Usage",
]
