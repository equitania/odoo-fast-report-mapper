# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import eq_utils
import click
from .__version__ import __version__, __author__, __url__
from .logging_config import get_logger, setup_logging
import logging

# Setup logging
setup_logging(level=logging.INFO)
logger = get_logger(__name__)


def print_banner():
    """Print professional banner with version information"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║               ⚡ Odoo FastReport Mapper & Testing Tool ⚡                    ║
║                                                                              ║
║  Version: {__version__:<15}                                                    ║
║  Author:  {__author__:<63} ║
║  URL:     {__url__:<63} ║
║                                                                              ║
║  FastReport Integration for Odoo - Mapping, Testing & Validation            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    click.echo(banner)


@click.command()
@click.version_option(version=__version__, prog_name="odoo-fast-report-mapper")
@click.option('--server_path', help='Server configuration folder',
              prompt='Please enter the path to your configuration folder')
@click.option('--yaml_path', help='Yaml folder',
              prompt='Please enter the path to your yaml folder')
def start_odoo_fast_report_mapper(server_path, yaml_path):
    """
    Odoo FastReport Mapper - Create and test FastReport entries in Odoo.

    This tool helps you manage FastReport configurations by:
    - Mapping report fields to Odoo models
    - Creating/updating FastReport entries
    - Testing report rendering
    - Managing calculated fields
    """
    # Print banner
    print_banner()
    # Collect yaml files and mapping existing yaml files
    connections = eq_utils.collect_all_connections(server_path)

    for connection in connections:
        connection.login()

        # Collect yaml
        if connection.collect_yaml:
            logger.info("Collecting YAML report entries...")
            connection.collect_all_report_entries(yaml_path)
        # Yaml Mapping
        else:
            reports = eq_utils.collect_all_reports(yaml_path)
            if connection.workflow == 0:
                logger.info("Starting report mapping...")
                connection.map_reports(reports)
            elif connection.workflow == 1:
                logger.info(f"Testing report rendering for database: {connection.database}")
                connection.test_fast_report_rendering(reports)
            elif connection.workflow == 2:
                logger.info("Starting report mapping...")
                connection.map_reports(reports)
                logger.info(f"Testing report rendering for database: {connection.database}")
                connection.test_fast_report_rendering(reports)
            else:
                logger.error("Invalid workflow configuration parameter value!")
                raise ValueError("Workflow must be 0 (mapping), 1 (testing), or 2 (both)")

        if connection.disable_qweb:
            logger.info("Disabling QWeb reports...")
            connection.disable_qweb_reports()

    logger.info("✅ Processing completed successfully!")
    click.echo("\n" + "="*80)
    click.echo("  ✅ All operations completed successfully!")
    click.echo("="*80 + "\n")


if __name__ == "__main__":
    start_odoo_fast_report_mapper()
