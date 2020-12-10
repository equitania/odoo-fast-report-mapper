# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import eq_utils
import click


def welcome():
    click.echo("Welcome to the odoo-fast-report-mapper!")


@click.command()
@click.option('--server_path', help='Server configuration folder',
              prompt='Please enter the path to your configuration folder')
@click.option('--report_path', help='Reports folder',
              prompt='Please enter the path to your report folder')
@click.option('--collect_reports', help='Report collection',
              prompt='Enter \"y\" for collection of reports')
def start_odoo_fast_report_mapper(server_path, report_path, collect_reports):
    # Collect yaml files and build objects
    connections = eq_utils.collect_all_connections(server_path)
    # Collect reports
    if collect_reports == 'y':
        for connection in connections:
            connection.login()
            connection.collect_all_report_entries(report_path)
    # Set reports
    else:
        reports = eq_utils.collect_all_reports(report_path)
        for connection in connections:
            connection.login()
            connection.clean_reports()
            click.echo("Mapping reports...")
            connection.map_reports(reports)
        click.echo("##### DONE #####")


if __name__ == "__main__":
    welcome()
    start_odoo_fast_report_mapper()
