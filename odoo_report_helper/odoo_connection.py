# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import urllib
from . import utils
import odoorpc
import sys
from . import exceptions


class OdooConnection:
    def __init__(self, url, port, username, password, database):
        self.username = username
        self.password = password
        self.database = database
        try:
            # Build connection
            self.connection = utils.prepare_connection(url, port)
        except urllib.error.URLError as ex:
            raise exceptions.OdooConnectionError(
                "ERROR: Please check your parameters and your connection" + " " + str(ex))
            sys.exit(0)

    def login(self):
        """
            Try to login into the Odoo system and set parameters to optimize the connection
        """
        try:
            self.connection.login(self.database, self.username, self.password)
            # Change settings to make the connection faster
            self.connection.config['auto_commit'] = True  # No need for manual commits
            self.connection.env.context['active_test'] = False  # Show inactive articles
            self.connection.env.context['tracking_disable'] = True
            print('##### Connected to ' + self.database + ' #####')
        except odoorpc.error.RPCError as ex:
            raise exceptions.OdooConnectionError(
                "ERROR: Please check your parameters and your connection" + " " + str(ex))
            sys.exit(0)

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

    def clear_reports(self):
        """
            Delete all reports with type "fast_report"
        """
        report_ids = self._get_fast_report_ids()
        for report_id in report_ids:
            self._delete_report(report_id)

    def set_calculated_fields(self, field_name, function_name, parameters, report_name, report_model):
        """
            Set calculated fields for the report and clean them:
            Example:
            {
                'field_name': {'function_name': ['parameter1', 'parameter2']},
                'payment_text': {'eq_get_payment_terms': ['partner_id.lang', 'currency_id']}
            }
        """
        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        REPORT_CALC = self.connection.env['eq_calculated_field_value']
        parameters_as_string = ', '.join(parameters)
        parameters_as_string = parameters_as_string.strip()
        value_dict = {"eq_field_name": field_name, "eq_function_name": function_name,
                      "eq_parameters_name": parameters_as_string}
        report_id = IR_ACTIONS_REPORT.search(
            [('model', '=', report_model), ('report_type', '=', 'fast_report'), '|', ('name', '=', report_name['ger']),
             ('name', '=', report_name['eng'])])
        value_dict["eq_report_id"] = report_id[0]
        calculated_field_id = REPORT_CALC.search(
            [('eq_report_id', '=', report_id[0]), ('eq_field_name', '=', field_name)])
        if len(calculated_field_id) == 0:
            REPORT_CALC.create(value_dict)
        else:
            calculated_field_id = calculated_field_id[0]
            calculated_field_object = REPORT_CALC.browse(calculated_field_id)
            calculated_field_object.write(value_dict)

    def _search_report(self, model_name, report_name):
        """
            Search for a report according to their report_name (non-case-sensitive) and model_name
            :param: model_name: Name of Odoo model
            :param: report_name: Name of report
            :return: First ID of found report(s)
        """
        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        report_ids = IR_ACTIONS_REPORT.search(
            [('model', '=', model_name), '|', ('name', '=ilike', report_name), ('name', '=ilike', report_name + " " + "(PDF)")])
        if len(report_ids) == 0:
            return False
        else:
            return report_ids[0]

    def _get_fast_report_ids(self):
        """
            Returns all report IDs that have report_type = fast_report
            :return: List of report_ids
        """
        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        report_ids = IR_ACTIONS_REPORT.search([('report_type', '=', "fast_report")])
        return report_ids

    def _delete_report(self, report_id):
        """
            Delete report and remove print_button in Odoo
            :param: report_id: ID of report in Odoo
        """
        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        report_object = IR_ACTIONS_REPORT.browse(report_id)
        report_object.unlink_action()
        report_object.unlink()

    def check_module(self, module_name):
        """
            Search for module in Odoo and return True when it is installed, else return false
            :param: module_name: Name of module
        """
        IR_MODULE_MODULE = self.connection.env['ir.module.module']
        module_id = IR_MODULE_MODULE.search([("state", "=", "installed"), ("name", "=", module_name)])
        if module_id:
            return True
        else:
            return False

    def check_dependencies(self, dependencies):
        """
            Check if all dependencies (modules) are installed, if one isn't, return False
            :param: dependencies: List of names of modules
        """
        if dependencies:
            for dependency in dependencies:
                dependency_installed = self.check_module(dependency)
                if not dependency_installed:
                    return False
        return True
