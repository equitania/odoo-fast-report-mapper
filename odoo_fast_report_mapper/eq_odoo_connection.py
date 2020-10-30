# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_report_helper.odoo_connection import OdooConnection


class EqOdooConnection(OdooConnection):
    def __init__(self, clean_old_reports, language, *args, **kwargs):
        super(EqOdooConnection, self).__init__(*args, **kwargs)
        self.do_clean_reports = clean_old_reports
        self.language = language

    def _search_report(self, model_name, report_name: dict):
        """
            If parameter "do_clean_reports" (delete_old_reports in connection yaml) is set, delete all report with
            report_type = fast_report
        """
        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        report_ids = IR_ACTIONS_REPORT.search([('model', '=ilike', model_name), '|', ('name', '=ilike', report_name['ger']),
                                               ('name', '=ilike', report_name['ger'] + " " + "(PDF)")])
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

    def map_reports(self, report_list: list):
        """
            Create/Write reports into the Odoo system with their fields and properties
            :param: report_list: List of report objects
        """
        IR_MODEL = self.connection.env['ir.model']
        IR_MODEL_FIELDS = self.connection.env['ir.model.fields']
        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        for report in report_list:
            report.self_ensure()
            report._data_dictionary['name'] = report.entry_name[self.language]
            dependencies_installed = self.check_dependencies(report._dependencies)
            if not dependencies_installed:
                print(f"!!! ******** DEPENDENCIES FOR {report.report_name} NOT INSTALLED ******** !!!")
                continue
            report_id = self._search_report(report.model_name, report.entry_name)
            if not report_id:
                report_id = IR_ACTIONS_REPORT.create(report._data_dictionary)
                report_object = IR_ACTIONS_REPORT.browse(report_id)
            else:
                report_object = IR_ACTIONS_REPORT.browse(report_id)
                report_object.write(report._data_dictionary)
            # Add report to print menu
            report_object.create_action()
            print(f"!!! ******** START {report.report_name} ******** !!!")
            try:
                # Loop over all models in report fields dictionary
                for model_name in report._fields:
                    # Get model object in Odoo
                    model_id = IR_MODEL.search([('model', '=', model_name)])
                    model_object = IR_MODEL.browse(model_id)
                    # Loop over all fields in the list of the current model
                    for field_name in report._fields[model_name]:
                        # Get the field from in Odoo
                        field_id = IR_MODEL_FIELDS.search(
                            [('model_id', '=', model_object.id), ('name', '=', field_name)])
                        if field_id:
                            field = IR_MODEL_FIELDS.browse(field_id)
                            # Insert the report_id
                            if report_object.id not in field.eq_report_ids.ids:
                                report_ids = field.eq_report_ids.ids
                                report_ids.append(report_object.id)
                                field.write({'eq_report_ids': [(6, 0, report_ids)]})
                if report._calculated_fields:
                    for field, content in report._calculated_fields.items():
                        for function_name, parameter in content.items():
                            self.set_calculated_fields(field, function_name, parameter, report.entry_name, report.model)
                print(f"!!! ******** END {report.report_name} ******** !!!")
            except Exception as ex:
                print("!!! ******** EXCEPTION ******** !!!")
                print(ex)
