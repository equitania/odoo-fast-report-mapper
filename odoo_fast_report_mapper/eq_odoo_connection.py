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
    def __init__(self, clean_old_reports, language, collect_yaml, disable_qweb, workflow, *args, **kwargs):
        super(EqOdooConnection, self).__init__(*args, **kwargs)
        self.do_clean_reports = clean_old_reports
        self.language = language
        self.collect_yaml = collect_yaml
        self.disable_qweb = disable_qweb
        self.workflow = workflow

    def _search_report_v13(self, model_name, report_name: dict, IR_ACTIONS_REPORT=False, company_id=False):
        """
            If parameter "do_clean_reports" (delete_old_reports in connection yaml) is set, delete all report with
            report_type = fast_report
        """
        if not IR_ACTIONS_REPORT:
            IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        report_ids = IR_ACTIONS_REPORT.search(
            [('model', '=ilike', model_name), '|', ('name', '=ilike', report_name['ger']),
             ('name', '=ilike', report_name['ger'] + " " + "(PDF)"),'|', ('company_id', '=', company_id), ('company_id', '=', False)])
        if len(report_ids) == 0 and 'eng' in report_name:
            report_ids = IR_ACTIONS_REPORT.search([('model', '=', model_name), '|', ('name', '=', report_name['eng']),
                                                   ('name', '=', report_name['eng'] + " " + "(PDF)"), '|', ('company_id', '=', company_id), ('company_id', '=', False)])
        if len(report_ids) == 0:
            return False
        else:
            return report_ids[0]

    def _search_report(self, model_name, report_name: dict, IR_ACTIONS_REPORT=False):
        """
            If parameter "do_clean_reports" (delete_old_reports in connection yaml) is set, delete all report with
            report_type = fast_report
        """
        if not IR_ACTIONS_REPORT:
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
        original_company_yaml_user = self.connection.env.user.company_id.id
        company_ids = self.connection.env.user.company_ids.ids if self.connection.env.user.company_ids else self.connection.env.user.company_id.ids
        for company_id in company_ids:
            self.connection.env.user.company_id = company_id
            if self.do_clean_reports:
                report_ids = self._get_fast_report_ids()
                for report_id in report_ids:
                    self._delete_report(report_id)
        self.connection.env.user.company_id = original_company_yaml_user

    def check_dependencies(self, dependencies):
        """
            Check if all dependencies (modules) are installed, if one isn't, return False
            :param: dependencies: List of names of modules
        """
        not_installed_modules = []
        if dependencies:
            for dependency in dependencies:
                dependency_installed = self.check_module(dependency)
                if not dependency_installed:
                    not_installed_modules.append(dependency)
            if not_installed_modules:
                return False, not_installed_modules
        return True, not_installed_modules

    def map_reports(self, report_list: list):
        """
            Create/Write reports into the Odoo system with their fields and properties
            :param: report_list: List of report objects
        """
        IR_MODEL = self.connection.env['ir.model']
        IR_MODEL_FIELDS = self.connection.env['ir.model.fields']
        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        original_company_yaml_user = IR_ACTIONS_REPORT.env.user.company_id
        for report in report_list:
            report.self_ensure()
            report._data_dictionary['name'] = report.entry_name[self.language]
            dependencies_installed, not_installed_modules = self.check_dependencies(report._dependencies)
            if not dependencies_installed and not_installed_modules:
                print(f"!!! ******** DEPENDENCIES FOR {report.report_name} NOT INSTALLED ******** !!!")
                for not_installed_module in not_installed_modules:
                    print(f"!!! ******** MODULE - {not_installed_module} - NOT INSTALLED ******** !!!")
                continue
            if report.company_id:
                IR_ACTIONS_REPORT.env.user.company_id = report.company_id[0]
                if self.version == '13':
                    report_id = self._search_report_v13(report.model_name, report.entry_name, IR_ACTIONS_REPORT, report.company_id[0])
                else:
                    report_id = self._search_report(report.model_name, report.entry_name, IR_ACTIONS_REPORT)
            else:
                report_id = self._search_report(report.model_name, report.entry_name, IR_ACTIONS_REPORT)
            if not report_id:
                report_id = IR_ACTIONS_REPORT.create(report._data_dictionary)
                report_object = IR_ACTIONS_REPORT.browse(report_id)
            else:
                report_object = IR_ACTIONS_REPORT.browse(report_id)
                report_object.write(report._data_dictionary)
            # Add report to print menu
            report_object.create_action()
            print(f"!!! ******** START {report.report_name} ******** !!!")
            IR_ACTIONS_REPORT.env.user.company_id = original_company_yaml_user
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
                                report_ids = field.eq_report_ids.ids + [report_object.id]
                                field.write({'eq_report_ids': [(6, 0, report_ids)]})
                                # field.update({'eq_report_ids': [(6, 0, report_ids)]})
                                # field.update({'eq_report_ids': [(4, report_object.id)]})
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
        company_ids = self.connection.env.user.company_ids.ids if self.connection.env.user.company_ids else self.connection.env.user.company_id.ids
        report_name_id_combination = dict()
        data_dictionary = {}
        for company_id in company_ids:
            # Change the current company in the env
            self.connection.env.user.company_id = company_id
            
            if self.version == "10":
                IR_ACTIONS_REPORT = self.connection.env['ir.actions.report.xml']
            else:
                IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
            data_dictionary_keys = list(data_dictionary.keys())
            report_ids = IR_ACTIONS_REPORT.search([('report_type', '=', 'fast_report'),('id', 'not in', data_dictionary_keys)])

            IR_MODEL_FIELDS = self.connection.env['ir.model.fields']
            all_report_field_ids = IR_MODEL_FIELDS.search([('eq_report_ids', 'in', report_ids), ('eq_report_ids', '!=', False)])

            # Get current company name
            company_name = self.connection.env['res.company'].browse(company_id).name
            print('Collect fields for %s' %company_name)
            
            # Progressbar...
            with click.progressbar(all_report_field_ids, length=len(all_report_field_ids)) as bar:
                for field_id in bar:
                    # Get object
                    field_object = IR_MODEL_FIELDS.browse(field_id)
                    # Get attributes
                    report_action_ids = field_object.eq_report_ids.ids
                    model_id = field_object.model_id
                    model_name = model_id.model
                    field_name = field_object.name


                    # Add field to dictionary
                    for report_action_id in report_action_ids:
                        report_action_object = IR_ACTIONS_REPORT.browse(report_action_id)
                        company_id = report_action_object.company_id.id if report_action_object.company_id else False
                        if company_id:
                            if report_action_object.report_name in report_name_id_combination and report_action_id != report_name_id_combination[report_action_object.report_name]:
                                if 'company_id' in data_dictionary[report_name_id_combination[report_action_object.report_name]] and company_id not in data_dictionary[report_name_id_combination[report_action_object.report_name]]['company_id']:
                                    data_dictionary[report_name_id_combination[report_action_object.report_name]]['company_id'].append(company_id)
                                continue
                            else:
                                report_name_id_combination[report_action_object.report_name] = report_action_id
                        data_dictionary = self.add_field_to_dictionary(data_dictionary, report_action_id, model_name,
                                                                    field_name, company_id)
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

    def add_field_to_dictionary(self, data_dictionary, report_id, model_name, field_name, company_id):
        if report_id not in data_dictionary:
            data_dictionary[report_id] = {}
        if model_name not in data_dictionary[report_id]:
            data_dictionary[report_id][model_name] = [field_name]
        if field_name not in data_dictionary[report_id][model_name]:
            data_dictionary[report_id][model_name].append(field_name)
        if company_id:
            if 'company_id' in data_dictionary[report_id] and company_id not in data_dictionary[report_id]['company_id']:
                data_dictionary[report_id]['company_id'].append(company_id)
            else:
                data_dictionary[report_id]['company_id'] = [company_id]
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

    def _collect_modules_dependencies_list(self, list_of_models):
        IR_MODELS = self.connection.env['ir.model']
        dependencies = []
        for model in list_of_models:
            model_id = IR_MODELS.search([('model','=', model)])
            model_obj = IR_MODELS.browse(model_id)
            models_dependencies = model_obj.modules.replace(' ', '').split(',')
            dependencies.extend(models_dependencies)
        # using set()
        # to remove duplicated 
        # from list
        return sorted(list(set(dependencies)))

    def create_eq_report_object(self, action_id, field_dictionary):
        if self.version == "10":
            IR_ACTIONS_REPORT = self.connection.env['ir.actions.report.xml']
        else:
            IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        if 'company_id' in field_dictionary:
            self.connection.env.user.company_id = field_dictionary['company_id'][0]
        action_object = IR_ACTIONS_REPORT.browse(action_id)
        # Collect attributes
        name = {self.language: action_object.name}
        if self.language != 'eng':
            name['eng'] = action_object.with_context(lang='en_US').name
        report_name = action_object.report_name
        report_type = action_object.report_type
        eq_export_type = action_object.eq_export_type
        print_report_name = action_object.print_report_name
        model_name = action_object.model
        eq_ignore_images = action_object.eq_ignore_images
        eq_handling_html_fields = action_object.eq_handling_html_fields
        multi = action_object.multi
        attachment_use = action_object.attachment_use
        attachment = action_object.attachment
        eq_calculated_field_ids = action_object.eq_calculated_field_ids
        company_id = field_dictionary['company_id'] if 'company_id' in field_dictionary else False
        if 'company_id' in field_dictionary:
            del field_dictionary['company_id']

        calculated_fields_dict = self._collect_calculated_fields(eq_calculated_field_ids)
        if not self.is_dict(calculated_fields_dict):
            calculated_fields_dict = {}
        eq_print_button = action_object.eq_print_button
        if not self.is_boolean(eq_print_button):
            eq_print_button = False
        eq_multiprint = action_object.eq_multiprint
        
        list_of_models = list(field_dictionary.keys())
        dependencies = self._collect_modules_dependencies_list(list_of_models)

        eq_report_obj = eq_report.EqReport(name, report_name, report_type, model_name, company_id, eq_export_type,
                                           print_report_name, attachment,
                                           eq_ignore_images, eq_handling_html_fields,
                                           multi,
                                           attachment_use, eq_print_button, dependencies, field_dictionary,
                                           calculated_fields_dict, eq_multiprint)
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
        original_company_yaml_user = self.connection.env.user.company_id
        for report in report_list:
            if report.company_id:
                self.connection.env.user.company_id = report.company_id[0]
                IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
                IR_MODEL = self.connection.env['ir.model']
                if self.version == '13':
                    report_id = self._search_report_v13(report.model_name, report.entry_name, IR_ACTIONS_REPORT, report.company_id[0])
                else:
                    report_id = self._search_report(report.model_name, report.entry_name, IR_ACTIONS_REPORT)
            else:
                IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
                IR_MODEL = self.connection.env['ir.model']
                report_id = self._search_report(report.model_name, report.entry_name, IR_ACTIONS_REPORT)
            # Get report action record
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
        self.connection.env.user.company_id = original_company_yaml_user

    def disable_qweb_reports(self):
        IR_ACTIONS_REPORT = self.connection.env['ir.actions.report']
        report_ids = IR_ACTIONS_REPORT.search(
            ['|', ('report_type', '=', 'qweb-pdf'), '|', ('report_type', '=', 'qweb-html'),
             ('report_type', '=', 'qweb-text')])
        for report_id in report_ids:
            report_object = IR_ACTIONS_REPORT.browse(report_id)
            report_object.unlink_action()
        print("Disabled QWeb for " + self.database)
