# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_report_helper.odoo_connection import OdooConnection


class EqOdooConnection(OdooConnection):
    def __init__(self, clean_old_reports, *args, **kwargs):
        super(EqOdooConnection, self).__init__(*args, **kwargs)
        self.do_clean_reports = clean_old_reports

    def _search_report(self, model_name, report_name: dict):
        """
            If parameter "do_clean_reports" (delete_old_reports in connection yaml) is set, delete all report with
            report_type = fast_report
        """
        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        report_ids = IR_ACTIONS_REPORT.search([('model', '=', model_name), '|', ('name', '=', report_name['ger']),
                                               ('name', '=', report_name['ger'] + " " + "(PDF)")])
        if len(report_ids) == 0:
            report_ids = IR_ACTIONS_REPORT.search([('model', '=', model_name), '|', ('name', '=', report_name['eng']),
                                                   ('name', '=', report_name['eng'] + " " + "(PDF)")])
        if len(report_ids) == 0:
            return False
        else:
            return report_ids[0]

    def clean_reports(self):
        """
            If parameter "do_clean_reports" (delete_old_reports in connection yaml) is set, delete all report with
            report_type = fast_report
        """
        if self.do_clean_reports:
            report_ids = self._get_fast_report_ids()
            for report_id in report_ids:
                self._delete_report(report_id)
