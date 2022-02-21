# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import eq_report
from . import eq_odoo_connection
import odoo_report_helper.utils as utils
import odoo_report_helper.exceptions as exceptions
import copy


def create_report_object_from_yaml_object(yaml_object):
    """
        Create EqReport object from yaml_object
        :param: yaml_object
        :return: EqReport object
    """
    # Set this in a try block because not all yaml files are up2date
    report = eq_report.EqReport(
        yaml_object['name'],
        yaml_object['report_name'],
        yaml_object['report_type'],
        yaml_object['report_model'],
        yaml_object.get('company_id', False),
        yaml_object['eq_export_type'],
        yaml_object['print_report_name'],
        yaml_object['attachment'],
        yaml_object['eq_ignore_images'],
        yaml_object['eq_handling_html_fields'],
        yaml_object['multi'],
        yaml_object['attachment_use'],
        yaml_object['eq_print_button'],
        yaml_object['dependencies'],
        yaml_object['report_fields'],
        yaml_object['calculated_fields'],
        yaml_object['eq_multiprint'],
    )
    return report


def create_odoo_connection_from_yaml_object(yaml_object):
    """
        Create EqOdooConnection object from yaml_object
        :param: yaml_object
        :return: EqOdooConnection object
    """
    eq_odoo_connection_object = eq_odoo_connection.EqOdooConnection(
        yaml_object['Server']['delete_old_reports'],
        yaml_object['Server']['language'],
        yaml_object['Server']['collect_yaml'] if 'collect_yaml' in yaml_object['Server'] else False,
        yaml_object['Server']['disable_qweb'] if 'disable_qweb' in yaml_object['Server'] else True,
        yaml_object['Server']['workflow'] if 'workflow' in yaml_object['Server'] else 0,
        yaml_object['Server']['url'],
        yaml_object['Server']['port'],
        yaml_object['Server']['user'],
        yaml_object['Server']['password'],
        yaml_object['Server']['database'],
    )
    return eq_odoo_connection_object


def convert_all_yaml_objects(yaml_objects: list, converting_function):
    """
        Convert list of yaml_objects through a converting function
        :param: list of yaml_objects
        :param: Function with which the yaml_objects should be converted
        :return: list of objects
    """
    local_object_list = []
    for yaml_object in yaml_objects:
        local_object = converting_function(yaml_object)
        local_object_list.append(local_object)
    return local_object_list


def collect_all_reports(path):
    """
        Get all yaml objects from path and convert them into report objects
        :param: path to yaml files
        :return: list of report objects
    """
    try:
        yaml_report_objects = utils.parse_yaml_folder(path)
        filtered_yaml_report_objects = []
        for yaml_report_object in yaml_report_objects:
            if yaml_report_object.get('company_id') and len(yaml_report_object.get('company_id')) > 1:
                company_ids = yaml_report_object.get('company_id')
                del yaml_report_object['company_id']
                for company_id in company_ids:
                    temp_yaml_report_object = copy.deepcopy(yaml_report_object)
                    temp_yaml_report_object['company_id'] = [company_id]
                    filtered_yaml_report_objects.append(temp_yaml_report_object)
            else:
                filtered_yaml_report_objects.append(yaml_report_object)
        eq_report_objects = convert_all_yaml_objects(filtered_yaml_report_objects, create_report_object_from_yaml_object)
        return eq_report_objects
    except FileNotFoundError as ex:
        raise exceptions.PathDoesNotExitError("ERROR: Please check your Path" + " " + str(ex))
        sys.exit(0)


def collect_all_connections(path):
    """
        Get all yaml objects from path and convert them into connection objects
        :param: path to yaml files
        :return: list of connection objects
    """
    try:
        yaml_connection_objects = utils.parse_yaml_folder(path)
        eq_connection_objects = convert_all_yaml_objects(yaml_connection_objects,
                                                         create_odoo_connection_from_yaml_object)
        return eq_connection_objects
    except FileNotFoundError as ex:
        raise exceptions.PathDoesNotExitError("ERROR: Please check your Path" + " " + str(ex))
        sys.exit(0)
