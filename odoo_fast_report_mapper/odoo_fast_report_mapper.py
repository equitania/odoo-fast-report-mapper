# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import eq_odoo_connection
import eq_report
import odooreporthelper.utils as utils
import eq_utils
import click

click.echo("Welcome to the odoo-fast-report-mapper!")


@click.command()
@click.option('--server_path', help='Server configuration folder', prompt='Please enter the path to your configuration folder')
@click.option('--report_path', help='Reports folder', prompt='Please enter the path to your report folder')
def main(server_path, report_path):
    print(server_path)
    print(report_path)
    connections = eq_utils.collect_all_connections(server_path)
    reports = eq_utils.collect_all_reports(report_path)
    for connection in connections:
        connection.login()
        connection.clean_reports()
        connection.map_reports(reports)
