# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import utils
import odoorpc
import sys
import exceptions


class Report:
    def __init__(self, entry_name: str, report_name: str, report_type: str, model_name: str, print_report_name="Report",
                 attachment="Report.pdf", attachment_use=False):
        self.entry_name = entry_name
        self.report_name = report_name
        self.report_type = report_type
        self.model_name = model_name
        self.print_report_name = print_report_name
        self.attachment = attachment
        self.attachment_use = attachment_use
        self._fields = {}
        self._calculated_fields = {}
        self._dependencies = []
        self._data_dictionary = {}

    def self_ensure(self):
        """
            Before mapping the fields, the value dictionary for Odoo must be set.
        """
        self._data_dictionary = {
            'name': self.entry_name,
            'report_name': self.report_name,
            'report_type': self.report_type,
            'print_report_name': self.print_report_name,
            'model': self.model_name,
            'attachment': self.attachment,
            'attachment_use': self.attachment_use
        }

    def add_fields(self, field_dict: dict):
        """
            Set fields for the report and clean them (remove duplicates).
            Example:
            {
                'account.invoice': ['id', 'name'],
                'sale.order: ['id', 'name'],
            }
            :param field_dict: Dictionary of models with their fields e.g.: {model: [field1, field2], model2...}
        """
        self._fields = utils.self_clean(field_dict)

    def add_calculated_fields(self, field_dict):
        """
            Set calculated fields for the report and clean them.
            :param field_dict: Dictionary of calculated fields e.g.:
            Example:
            {
                'field_name': {'function_name': ['parameter1', 'parameter2']},
                'payment_text': {'eq_get_payment_terms': ['partner_id.lang', 'currency_id']}
            }
        """
        self._calculated_fields = field_dict

    def add_dependencies(self, dependency_list: list):
        self._dependencies = dependency_list



