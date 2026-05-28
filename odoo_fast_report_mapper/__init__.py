from .__version__ import (
    __author__,
    __author_email__,
    __copyright__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
    __version_info__,
)
from ._connection import OdooConnection
from ._exceptions import OdooConnectionError, PathDoesNotExistError, PathDoesNotExitError
from ._report import Report
from ._utils import create_connection_from_env

__all__ = [
    "OdooConnection",
    "Report",
    "create_connection_from_env",
    "OdooConnectionError",
    "PathDoesNotExistError",
    "PathDoesNotExitError",
    "__version__",
    "__version_info__",
    "__title__",
    "__description__",
    "__author__",
    "__author_email__",
    "__url__",
    "__license__",
    "__copyright__",
]
