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
import base64
from random import choice
import sys
import logging


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
        report_ids = IR_ACTIONS_REPORT.search(
            [('model', '=ilike', model_name), '|', ('name', '=ilike', report_name['ger']),
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
                            self.set_calculated_fields(field, function_name, parameter, report.entry_name,
                                                       report.model_name)
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
                    data_dictionary = self.add_field_to_dictionary(data_dictionary, report_action_id, model_name,
                                                                   field_name)
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
        if self.version == "10":
            IR_ACTIONS_REPORT = self.connection.env['ir.actions.report.xml']
        else:
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
        multi_print = action_object.multi
        attachment_use = action_object.attachment_use
        attachment = action_object.attachment
        eq_calculated_field_ids = action_object.eq_calculated_field_ids
        company_id = action_object.company_id

        # Special cases => not in every version
        eq_export_as_sql = action_object.eq_export_as_sql
        if not self.is_boolean(eq_export_as_sql):
            eq_export_as_sql = True
        calculated_fields_dict = self._collect_calculated_fields(eq_calculated_field_ids)
        if not self.is_dict(calculated_fields_dict):
            calculated_fields_dict = {}
        eq_print_button = action_object.eq_print_button
        if not self.is_boolean(eq_print_button):
            eq_print_button = False
        eq_merge_data_from_multi = action_object.eq_merge_data_from_multi
        if not self.is_boolean(eq_merge_data_from_multi):
            eq_merge_data_from_multi = False

        eq_report_obj = eq_report.EqReport(name, report_name, report_type, model_name, company_id, eq_export_type,
                                           print_report_name, attachment,
                                           eq_ignore_images, eq_ignore_html, eq_export_complete_html, eq_export_as_sql,
                                           multi_print,
                                           attachment_use, eq_print_button, [], field_dictionary,
                                           calculated_fields_dict, eq_merge_data_from_multi)
        return eq_report_obj

    def write_yaml(self, file_name, data):
        with io.open(file_name, 'w', encoding='utf8') as outfile:
            yaml.dump(data, outfile, Dumper=MyDumper.MyDumper, default_flow_style=False, allow_unicode=True,
                      sort_keys=False)

    def is_boolean(self, object_to_be_checked):
        if isinstance(object_to_be_checked, bool):
            return True
        return False

    def is_dict(self, object_to_be_checked):
        if isinstance(object_to_be_checked, dict):
            return True
        return False

    def test_fast_report_rendering(self, report_list: list):
        """
            Test FastReport rendering in the Odoo system
            :param: report_list: List of report objects
            IMPORTANT: The FastReport API URL, conection and base report setup must be done before testing.
        """

        ### Uncomment/comment to display logging to extern log file or to console ###
        ## Log file
        #logging.basicConfig(format='%(asctime)s - %(message)s ',  datefmt='%H:%M:%S %d.%m.%Y', level=logging.INFO, filename=f"testing_fast_report_rendering_{self.connection._env._db}.log")
        ## Console
        logging.basicConfig(format='%(asctime)s - %(message)s ',  datefmt='%H:%M:%S %d.%m.%Y', level=logging.INFO)

        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        IR_MODEL = self.connection.env['ir.model']
        for report in report_list:
            # Get report action record
            report_id = self._search_report(report.model_name, report.entry_name)
            report_object = IR_ACTIONS_REPORT.browse(report_id) if report_id else False
            # Check if the report has been created and is type Fast Report
            if not report_id or report_object.report_type != "fast_report": 
                logging.info(f"!!! ******** REPORT {report.report_name} NOT CREATED OR IS NOT TYPE FAST REPORT ******** !!!")
                continue

            logging.info(f"!!! ******** TESTING REPORT RENDERING {report.report_name} ******** !!!")

            ## Get module from report model
            IR_REPORT_MODEL = self.connection.env[report.model_name]
            
            ''' This is extra help: display modules from report model and report filename code
            # Get the report model object
            model_id = IR_MODEL.search([('model', '=', report.model_name)])
            report_model_object = IR_MODEL.browse(model_id)
            report_modules = report_model_object['modules']
            logging.info(f"MODULES USING MODEL {report.model_name} FROM REPORT {report.report_name} WITH FILENAME {report.print_report_name}")
            logging.info(report_modules)
            Can be comented if not necessary '''

            if report_object:
                # Get all report model records ids 
                report_model_records_ids = IR_REPORT_MODEL.search([])
                try:
                    if not len(report_model_records_ids):
                        logging.info(f"\033[0;33m!!! ******** NO RECORDS FOR MODEL {report.model_name} ******** !!!\033[0;37m")
                        logging.info(f"\033[0;33m!!! ******** USING DEMO DATA TO TEST REPORT {report.report_name} ******** !!!\033[0;37m")
                        # Render Fast Report for demo example databases
                        res, content_format = IR_ACTIONS_REPORT.eq_render_fast_report_empty_db(report_object.ids)
                    else:
                        # Render Fast Report for a random report model record, without creating attachment
                        res, content_format = IR_ACTIONS_REPORT.eq_render_fast_report(report_object.ids, [choice(report_model_records_ids)], create_attachment=False)
                    # Convert data content to base64
                    data = base64.encodebytes(res.encode('utf-8')).decode('utf-8')
                    logging.info(f"\033[0;92m!!! ******** REPORTS RENDERING {report.report_name} OK ******** !!!\033[0;37m")
                except Exception as ex:
                    if "No such file or directory" in str(ex):
                        logging.info(f"\033[0;33m!!! ******** NO DEMO DATA TO TEST REPORT {report.report_name} ******** !!!\033[0;37m ")
                    else:
                        logging.info(f"\033[0;31m!!! ******** REPORT \033[1;31m{report.report_name}\033[0;31m NOT RENDERING CORRECTLY ******** !!!\033[0;37m ")
                        logging.info(f"\033[0;31m!!! ******** EXCEPTION ******** !!!\033[0;37m")
                        logging.info("\033[0;31m" + str(ex) + "\033[0;37m")
