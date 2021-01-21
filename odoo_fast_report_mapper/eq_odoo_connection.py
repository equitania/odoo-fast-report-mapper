# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import click
from odoo_report_helper.odoo_connection import OdooConnection
from . import eq_report
from datetime import datetime
import io
import yaml
from . import MyDumper


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
        if len(report_ids) == 0 and 'eng' in report_name:
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
                            self.set_calculated_fields(field, function_name, parameter, report.entry_name, report.model_name)
                print(f"!!! ******** END {report.report_name} ******** !!!")
            except Exception as ex:
                print("!!! ******** EXCEPTION ******** !!!")
                print(ex)

    def collect_all_report_entries(self, output_path):
        IR_MODEL_FIELDS = self.connection.env['ir.model.fields']
        all_report_field_ids = IR_MODEL_FIELDS.search([('eq_report_ids', '!=', False)])
        data_dictionary = {}
        print('Collect fields...')
        # Progressbar...
        with click.progressbar(range(len(all_report_field_ids))) as bar:
            for field_id in all_report_field_ids:
                # Get object
                field_object = IR_MODEL_FIELDS.browse(field_id)
                # Get attributes
                report_action_ids = field_object.eq_report_ids.ids
                model_id = field_object.model_id
                model_name = model_id.model
                field_name = field_object.name
                # Add field to dictionary
                for report_action_id in report_action_ids:
                    data_dictionary = self.add_field_to_dictionary(data_dictionary, report_action_id, model_name, field_name)
        for report_action_id, fields in data_dictionary.items():
            # Create report object
            eq_report_object = self.create_eq_report_object(report_action_id, fields)
            eq_yaml_data = eq_report_object.ensure_data_for_yaml()
            # Get timestamp
            now = datetime.now()
            date_now = now.strftime("%m_%d_%Y_%H_%M_%S")
            # Set output name
            output_name = output_path + '/' + eq_report_object.report_name + '_' + date_now + '.yaml'
            self.write_yaml(output_name, eq_yaml_data)

    def add_field_to_dictionary(self, data_dictionary, report_id, model_name, field_name):
        if report_id not in data_dictionary:
            data_dictionary[report_id] = {}
        if model_name not in data_dictionary[report_id]:
            data_dictionary[report_id][model_name] = [field_name]
        else:
            data_dictionary[report_id][model_name].append(field_name)
        return data_dictionary

    def _collect_calculated_fields(self, eq_calculated_field_objects):
        """
            Get calculated fields from eq_calculated_field model objects:
            Example:
            {
                'field_name': {'function_name': ['parameter1', 'parameter2']},
            }
        """
        eq_calculated_field_dict = {}

        for eq_calculated_field in eq_calculated_field_objects:
            eq_calculated_field_field_name = eq_calculated_field.eq_field_name
            eq_calculated_field_func_name = eq_calculated_field.eq_function_name
            eq_calculated_field_params_name = eq_calculated_field.eq_parameters_name
            eq_calculated_field_dict[eq_calculated_field_field_name] = {
                eq_calculated_field_func_name: eq_calculated_field_params_name.replace(" ", "").split(',')
            }
        return eq_calculated_field_dict

    def create_eq_report_object(self, action_id, field_dictionary):
        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        action_object = IR_ACTIONS_REPORT.browse(action_id)
        # Collect attributes
        name = {self.language: action_object.name}
        report_name = action_object.report_name
        report_type = action_object.report_type
        eq_export_type = action_object.eq_export_type
        print_report_name = action_object.print_report_name
        model_name = action_object.model
        eq_ignore_images = action_object.eq_ignore_images
        eq_ignore_html = action_object.eq_ignore_html
        eq_export_complete_html = action_object.eq_export_complete_html
        eq_export_as_sql = action_object.eq_export_as_sql
        multi_print = action_object.multi
        attachment_use = action_object.attachment_use
        eq_print_button = action_object.eq_print_button
        eq_merge_data_from_multi = action_object.eq_merge_data_from_multi
        attachment = action_object.attachment
        # Get calculated fields
        eq_calculated_field_ids = action_object.eq_calculated_field_ids
        calculated_fields_dict = self._collect_calculated_fields(eq_calculated_field_ids)
        eq_report_obj = eq_report.EqReport(name, report_name, report_type, model_name, eq_export_type, print_report_name, attachment,
                             eq_ignore_images, eq_ignore_html, eq_export_complete_html, eq_export_as_sql, multi_print,
                             attachment_use, eq_print_button, [], field_dictionary, calculated_fields_dict, eq_merge_data_from_multi)
        return eq_report_obj

    def write_yaml(self, file_name, data):
        with io.open(file_name, 'w', encoding='utf8') as outfile:
            yaml.dump(data, outfile, Dumper=MyDumper.MyDumper, default_flow_style=False, allow_unicode=True, sort_keys=False)