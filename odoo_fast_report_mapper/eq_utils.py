# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from eq_report import EqReport


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
        yaml_object['eq_print_button']
    )
    return report


def collect_all_reports_from_yaml_objects(yaml_objects: list):
    report_object_list = []
    for yaml_object in yaml_objects:
        report_object = create_report_object_from_yaml_object(yaml_object)
        report_object_list.append(report_object)
    return report_object_list
