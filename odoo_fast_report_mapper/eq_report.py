# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_report_helper.report import Report


class EqReport(Report):
    def __init__(self, entry_name, report_name: str, report_type: str, model_name: str, company_id, eq_export_type="pdf",
                 print_report_name="Report", attachment="Report.pdf", eq_ignore_images=True, eq_handling_html_fields='standard', multi=False, attachment_use=False,
                 eq_print_button=False, dependencies=False, model_fields={}, calculated_fields={},
                 eq_multiprint='standard'):
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
        self._data_dictionary = {}
        self.company_id = company_id

    def self_ensure(self):
        """
            Before mapping the fields, the value dictionary for Odoo must be set.
        """
        self._data_dictionary = {
            'name': self.entry_name['ger'],
            'report_name': self.report_name,
            'report_type': self.report_type,
            'print_report_name': self.print_report_name,
            'model': self.model_name,
            'company_id': self.company_id[0] if self.company_id else False,
            'eq_export_type': self.eq_export_type,
            'eq_ignore_images': self.eq_ignore_images,
            'eq_handling_html_fields': self.eq_handling_html_fields,
            'eq_multiprint': self.eq_multiprint,
            'multi': self.multi,
            'attachment': self.attachment,
            'attachment_use': self.attachment_use,
            'eq_print_button': self.eq_print_button
        }

    def ensure_data_for_yaml(self):
        yaml_data = {
            'name': self.entry_name,
            'report_name': self.report_name,
            'report_type': self.report_type,
            'print_report_name': self.print_report_name,
            'report_model': self.model_name,
            'eq_export_type': self.eq_export_type,
            'eq_ignore_images': self.eq_ignore_images,
            'eq_handling_html_fields': self.eq_handling_html_fields,
            'eq_multiprint': self.eq_multiprint,
            'multi': self.multi,
            'attachment': self.attachment,
            'attachment_use': self.attachment_use,
            'eq_print_button': self.eq_print_button,
            'dependencies': self._dependencies,
            'report_fields': self._fields,
            'calculated_fields': self._calculated_fields
        }
        if self.company_id:
            yaml_data = {k: v for k, v in (list(yaml_data.items())[:5] + [('company_id', self.company_id)] + list(yaml_data.items())[5:])}
        return yaml_data
