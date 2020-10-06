# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import eq_odoo_connection
import eq_report
import odooreporthelper.utils as utils
import eq_utils

reports_folder = "/reports_yaml"

# Collect reports
yaml_objects = utils.parse_yaml_folder(reports_folder)
eq_report_objects = eq_utils.collect_all_reports_from_yaml_objects(yaml_objects)

