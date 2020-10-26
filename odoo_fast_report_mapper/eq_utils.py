# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from eq_report import EqReport
from eq_odoo_connection import EqOdooConnection
import utils
import exceptions


def create_report_object_from_yaml_object(yaml_object):
    report = EqReport(
        yaml_object['name'],
        yaml_object['report_name'],
        yaml_object['report_type'],
        yaml_object['report_model'],
        yaml_object['eq_export_type'],
        yaml_object['print_report_name'],
        yaml_object['attachment'],
        yaml_object['eq_ignore_images'],
        yaml_object['eq_ignore_html'],
        yaml_object['eq_export_complete_html'],
        yaml_object['eq_export_as_sql'],
        yaml_object['multiprint'],
        yaml_object['attachment_use'],
        yaml_object['eq_print_button'],
        yaml_object['dependencies'],
        yaml_object['report_fields'],
        yaml_object['calculated_fields']
    )
    return report


def create_odoo_connection_from_yaml_object(yaml_object):
    eq_odoo_connection = EqOdooConnection(
        yaml_object['Server']['delete_old_reports'],
        yaml_object['Server']['url'],
        yaml_object['Server']['port'],
        yaml_object['Server']['user'],
        yaml_object['Server']['password'],
        yaml_object['Server']['database'],
    )
    return eq_odoo_connection


def convert_all_yaml_objects(yaml_objects: list, converting_function):
    local_object_list = []
    for yaml_object in yaml_objects:
        local_object = converting_function(yaml_object)
        local_object_list.append(local_object)
    return local_object_list


def collect_all_reports(path):
    try:
        yaml_report_objects = utils.parse_yaml_folder(path)
        eq_report_objects = convert_all_yaml_objects(yaml_report_objects, create_report_object_from_yaml_object)
        return eq_report_objects
    except FileNotFoundError as ex:
        raise exceptions.PathDoesNotExitError("ERROR: Please check your Path" + " " + str(ex))
        sys.exit(0)


def collect_all_connections(path):
    try:
        yaml_connection_objects = utils.parse_yaml_folder(path)
        eq_connection_objects = convert_all_yaml_objects(yaml_connection_objects, create_odoo_connection_from_yaml_object)
        return eq_connection_objects
    except FileNotFoundError as ex:
        raise exceptions.PathDoesNotExitError("ERROR: Please check your Path" + " " + str(ex))
        sys.exit(0)
