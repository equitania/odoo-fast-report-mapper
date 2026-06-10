# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""TypedDict type definitions for Odoo RPC response shapes. Internal use only."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class IrModelRecord(TypedDict, total=True):
    """ir.model record returned by Odoo RPC search_read calls."""

    id: int
    model: str
    name: str


class IrModelFieldsRecord(TypedDict, total=False):
    """ir.model.fields record. total=False: not all fields guaranteed in all Odoo versions."""

    id: int
    name: str
    ttype: str
    modules: str | Literal[False]  # Odoo returns False when no module owns the field


class ReportAction(TypedDict, total=True):
    """ir.actions.report record returned by browse/search_read."""

    id: int
    report_type: str
    model: str
    name: str
    ids: list[int]


class LanguageRecord(TypedDict, total=True):
    """res.lang record from get_installed_languages."""

    code: str
    name: str
