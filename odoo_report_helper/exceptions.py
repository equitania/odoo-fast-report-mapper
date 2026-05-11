# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


class OdooConnectionError(Exception):
    pass


class PathDoesNotExistError(Exception):
    pass


# Backward-compatibility alias for the historical misspelling (typo: "Exit" → "Exist")
PathDoesNotExitError = PathDoesNotExistError
