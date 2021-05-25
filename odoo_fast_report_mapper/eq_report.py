# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_report_helper.report import Report


class EqReport(Report):
    def __init__(self, entry_name, report_name: str, report_type: str, model_name: str, eq_export_type="pdf",
                 print_report_name="Report",attachment="Report.pdf", eq_ignore_images=True, eq_ignore_html=False,
                 eq_export_complete_html=False,eq_export_as_sql=True, multi_print=False, attachment_use=False,
                 eq_print_button=False, dependencies=[], model_fields={}, calculated_fields={}, eq_merge_data_from_multi=False):
        self.entry_name = entry_name
        self.report_name = report_name
        self.report_type = report_type
        self.model_name = model_name
        self.print_report_name = print_report_name
        self.eq_export_type = eq_export_type
        self.attachment = attachment
        self.eq_ignore_images = eq_ignore_images
        self.eq_ignore_html = eq_ignore_html
        self.eq_export_complete_html = eq_export_complete_html
        self.eq_export_as_sql = eq_export_as_sql
        self.multi_print = multi_print
        self.attachment_use = attachment_use
        self.eq_merge_data_from_multi = eq_merge_data_from_multi
        self.eq_print_button = eq_print_button
        self._fields = model_fields
        self._calculated_fields = calculated_fields
        self._dependencies = dependencies
        self._data_dictionary = {}

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
            'eq_export_type': self.eq_export_type,
            'eq_ignore_images': self.eq_ignore_images,
            'eq_ignore_html': self.eq_ignore_html,
            'eq_export_complete_html': self.eq_export_complete_html,
            'eq_export_as_sql': self.eq_export_as_sql,
            'eq_merge_data_from_multi': self.eq_merge_data_from_multi,
            'multi': self.multi_print,
            'attachment': self.attachment,
            'attachment_use': self.attachment_use,
            'eq_print_button': self.eq_print_button
        }

    def ensure_data_for_yaml(self):
        yaml_data = {'name': self.entry_name,
            'report_name': self.report_name,
            'report_type': self.report_type,
            'print_report_name': self.print_report_name,
            'report_model': self.model_name,
            'eq_export_type': self.eq_export_type,
            'eq_ignore_images': self.eq_ignore_images,
            'eq_ignore_html': self.eq_ignore_html,
            'eq_export_complete_html': self.eq_export_complete_html,
            'eq_export_as_sql': self.eq_export_as_sql,
            'eq_merge_data_from_multi': self.eq_merge_data_from_multi,
            'multiprint': self.multi_print,
            'attachment': self.attachment,
            'attachment_use': self.attachment_use,
            'eq_print_button': self.eq_print_button,
            'dependencies': [],
            'report_fields': self._fields,
            'calculated_fields': self._calculated_fields
        }
        return yaml_data