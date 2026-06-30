# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import annotations


class OdooConnectionError(Exception):
    """Raised when establishing or using the Odoo RPC connection fails."""


class PathDoesNotExistError(Exception):
    """Raised when a required file system path (e.g. a YAML directory) does not exist."""


# Backward-compatibility alias for the historical misspelling (typo: "Exit" → "Exist")
PathDoesNotExitError = PathDoesNotExistError
