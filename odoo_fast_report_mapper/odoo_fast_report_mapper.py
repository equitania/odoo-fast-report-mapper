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
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              ⚡ Odoo FastReport Mapper & Testing Tool ⚡                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    click.echo(banner)
    click.echo(f"  Version: {__version__}")
    click.echo(f"  Author:  {__author__}")
    click.echo(f"  URL:     {__url__}")
    click.echo()
    click.echo("  FastReport Integration for Odoo - Mapping, Testing & Validation")
    click.echo()


@click.command()
@click.version_option(version=__version__, prog_name="odoo-fast-report-mapper")
@click.option('--yaml_path', help='Path to YAML report definitions folder',
              prompt='Please enter the path to your YAML reports folder')
@click.option('--env_path', default=None, help='Path to .env file (default: current directory)')
def start_odoo_fast_report_mapper(yaml_path, env_path):
    """
    Odoo FastReport Mapper - Create and test FastReport entries in Odoo.

    This tool helps you manage FastReport configurations by:
    - Mapping report fields to Odoo models
    - Creating/updating FastReport entries
    - Testing report rendering
    - Managing calculated fields

    Configuration:
    - Connection settings are read from .env file
    - Copy .env.example to .env and configure your Odoo connection
    - Report definitions are read from YAML files in yaml_path
    """
    # Print banner
    print_banner()

    # Create connection from .env file
    try:
        connection = eq_utils.create_connection_from_env(env_path=env_path)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        click.echo("\n" + "="*80)
        click.echo("  ❌ Failed to load connection configuration")
        click.echo("  💡 Please create a .env file based on .env.example")
        if env_path:
            click.echo(f"  📁 Searched in: {env_path}")
        else:
            click.echo("  📁 Searched in: current directory")
        click.echo("="*80 + "\n")
        return

    # Login to Odoo
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
