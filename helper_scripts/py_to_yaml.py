# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import io
import yaml
import report_as_py as report

file_name = report.report_tmpl_name + '.yaml'

data = {}
# Start with yaml variables
data['name'] = report.report_name
data['report_name'] = report.report_tmpl_name
data['report_model'] = report.report_model
data['attachment'] = report.attachment
data['print_report_name'] = report.print_report_name
data['report_type'] = 'fast_report'
data['eq_export_type'] = 'pdf'
data['eq_ignore_images'] = True
data['eq_ignore_html'] = False
data['eq_export_complete_html'] = False
data['eq_export_as_sql'] = True
data['eq_print_button'] = report.eq_print_report_button
data['multiprint'] = False
data['attachment_use'] = True

data['dependencies'] = ['eq_base', 'eq_fr_core', 'eq_res_partner',
                        ]

data['report_fields'] = report.report_fields

data['calculated_fields'] = {}


with io.open(file_name, 'w', encoding='utf8') as outfile:
    yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True, sort_keys=False)