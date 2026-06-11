# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Report data container for FastReport YAML-to-Odoo mapping."""

from __future__ import annotations

from typing import Any, Literal

from ._lang_utils import get_primary_lang
from ._utils import self_clean


class Report:
    # Note: this class has no base class after consolidation. No super-init call is needed.
    def __init__(
        self,
        entry_name: dict[str, str],
        report_name: str,
        report_type: str,
        model_name: str,
        company_id: list[int] | Literal[False],
        eq_export_type: str = "pdf",
        print_report_name: str | dict[str, str] = "Report",
        attachment: str | dict[str, str] = "Report.pdf",
        eq_ignore_images: bool = True,
        eq_handling_html_fields: str = "standard",
        multi: bool = False,
        attachment_use: bool = False,
        eq_print_button: bool = False,
        dependencies: list[str] | Literal[False] = False,
        model_fields: dict[str, list[str]] | None = None,
        calculated_fields: dict[str, Any] | None = None,
        eq_multiprint: str = "standard",
    ) -> None:
        if not isinstance(entry_name, dict) or not entry_name:
            raise TypeError(
                f"entry_name must be a non-empty dict mapping language codes to names, got {type(entry_name).__name__}"
            )
        if calculated_fields is None:
            calculated_fields = {}
        if model_fields is None:
            model_fields = {}
        self.entry_name = entry_name
        self.report_name = report_name
        self.report_type = report_type
        self.model_name = model_name
        self.print_report_name = print_report_name
        self.eq_export_type = eq_export_type
        self.attachment = attachment
        self.eq_ignore_images = eq_ignore_images
        self.eq_handling_html_fields = eq_handling_html_fields
        self.multi = multi
        self.attachment_use = attachment_use
        self.eq_multiprint = eq_multiprint
        self.eq_print_button = eq_print_button
        self._fields = model_fields
        self._calculated_fields = calculated_fields
        self._dependencies = dependencies
        self._data_dictionary: dict[str, Any] = {}  # Any: mixed Odoo field values
        self.company_id = company_id

    def self_ensure(self) -> None:
        """
        Before mapping the fields, the value dictionary for Odoo must be set.
        """
        primary_lang = get_primary_lang(self.entry_name)
        self._data_dictionary = {
            "name": self.entry_name[primary_lang],
            "report_name": self.report_name,
            "report_type": self.report_type,
            "print_report_name": (
                self.print_report_name[get_primary_lang(self.print_report_name)]
                if isinstance(self.print_report_name, dict)
                else self.print_report_name
            ),
            "model": self.model_name,
            "company_id": self.company_id[0] if self.company_id else False,
            "eq_export_type": self.eq_export_type,
            "eq_ignore_images": self.eq_ignore_images,
            "eq_handling_html_fields": self.eq_handling_html_fields,
            "eq_multiprint": self.eq_multiprint,
            "multi": self.multi,
            "attachment": (
                self.attachment[get_primary_lang(self.attachment)]
                if isinstance(self.attachment, dict)
                else self.attachment
            ),
            "attachment_use": self.attachment_use,
            "eq_print_button": self.eq_print_button,
        }

    def ensure_data_for_yaml(self) -> dict[str, Any]:
        yaml_data = {
            "name": self.entry_name,
            "report_name": self.report_name,
            "report_type": self.report_type,
            "print_report_name": self.print_report_name,
            "report_model": self.model_name,
            "eq_export_type": self.eq_export_type,
            "eq_ignore_images": self.eq_ignore_images,
            "eq_handling_html_fields": self.eq_handling_html_fields,
            "eq_multiprint": self.eq_multiprint,
            "multi": self.multi,
            "attachment": self.attachment,
            "attachment_use": self.attachment_use,
            "eq_print_button": self.eq_print_button,
            "dependencies": self._dependencies,
            "report_fields": self._fields,
            "calculated_fields": self._calculated_fields,
        }
        if self.company_id:
            yaml_data = {
                k: v
                for k, v in (
                    list(yaml_data.items())[:5] + [("company_id", self.company_id)] + list(yaml_data.items())[5:]
                )
            }
        return yaml_data

    def add_fields(self, field_dict: dict[str, list[str]]) -> None:
        """
        Set fields for the report and clean them (remove duplicates).
        Example:
        {
            'account.invoice': ['id', 'name'],
            'sale.order: ['id', 'name'],
        }
        :param field_dict: Dictionary of models with their fields e.g.: {model: [field1, field2], model2...}
        """
        for model, fields in field_dict.items():
            self._fields[model] = fields
        self._fields = self_clean(self._fields)

    def add_calculated_fields(self, field_dict: dict[str, Any]) -> None:
        """
        Add calculated fields for the report.
        :param field_dict: Dictionary of calculated fields e.g.:
        Example:
        {
            'field_name': {'function_name': ['parameter1', 'parameter2']},
            'payment_text': {'eq_get_payment_terms': ['partner_id.lang', 'currency_id']}
        }
        """
        for field_name, content in field_dict.items():
            self._calculated_fields[field_name] = content
        # Do NOT call self_clean — values are dicts {function_name: [params]}, not lists;
        # outer keys are unique by dict semantics, so no deduplication is needed.

    def add_dependencies(self, dependency_list: list[str]) -> None:
        """
        Add dependencies to self._dependencies
        """
        existing: list[str] = self._dependencies if isinstance(self._dependencies, list) else []
        # Remove duplicates with deterministic ordering for reproducible YAML output
        self._dependencies = sorted(set(existing + dependency_list))
