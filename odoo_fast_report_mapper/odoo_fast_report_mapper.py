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
@click.option('--yaml_path', help='Yaml folder',
              prompt='Please enter the path to your yaml folder')
def start_odoo_fast_report_mapper(server_path, yaml_path):
    # Collect yaml files and mapping existing yaml files
    connections = eq_utils.collect_all_connections(server_path)

    for connection in connections:
        connection.login()

        # Collect yaml
        if connection.collect_yaml:
            connection.collect_all_report_entries(yaml_path)
        # Yaml Mapping
        else:
            reports = eq_utils.collect_all_reports(yaml_path)
            if connection.workflow == 0:
                connection.clean_reports()
                click.echo("Mapping reports...")
                connection.map_reports(reports)
            elif connection.workflow == 1:
                click.echo(f"\nTesting reports rendering for database: {connection.database}")
                connection.test_fast_report_rendering(reports)
            elif connection.workflow == 2:
                connection.clean_reports()
                click.echo("Mapping reports...")
                connection.map_reports(reports)
                click.echo(f"\nTesting reports rendering for database: {connection.database}")
                connection.test_fast_report_rendering(reports)
            else:
                click.echo("The value of the configuration parameter workflow is wrong!")

        if connection.disable_qweb:
            connection.disable_qweb_reports()

    click.echo("##### DONE #####")


if __name__ == "__main__":
    welcome()
    start_odoo_fast_report_mapper()
