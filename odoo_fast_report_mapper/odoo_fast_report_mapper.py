# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os

import click

from . import eq_utils
from .__version__ import __author__, __url__, __version__
from .logging_config import get_logger, setup_logging

# Setup logging
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

WORKFLOW_LABELS = {
    0: "Mapping only",
    1: "Testing only",
    2: "Mapping + Testing",
}


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


def init_callback(ctx, param, value):
    """Handle --init flag before other prompts."""
    if not value:
        return
    target_dir = os.getcwd()
    try:
        env_file = eq_utils.generate_env_template(target_dir)
        click.echo(f"  Created .env template at: {env_file}")
        click.echo("  Edit the file with your Odoo connection details")
    except FileExistsError as e:
        click.echo(f"  Warning: {e}")
    ctx.exit()


@click.command()
@click.version_option(version=__version__, prog_name="odoo-fast-report-mapper")
@click.option(
    "--init",
    is_flag=True,
    callback=init_callback,
    expose_value=False,
    is_eager=True,
    help="Generate .env template in current directory and exit.",
)
@click.option(
    "--yaml_path",
    help="Path to folder containing YAML report definition files.",
    prompt="Please enter the path to your YAML reports folder",
)
@click.option(
    "--env_path",
    default=None,
    help="Path to .env file or directory containing it. Default: current directory.",
)
@click.option(
    "--select",
    is_flag=True,
    default=False,
    help="Show interactive table of YAML files and select which to process (e.g. 1,3,5 or 'all').",
)
def start_odoo_fast_report_mapper(yaml_path, env_path, select):
    """Odoo FastReport Mapper - Map, test and manage FastReport entries in Odoo.

    \b
    WORKFLOWS (configured via ODOO_WORKFLOW in .env):
      0 = Mapping only (default) - Create/update ir.actions.report records
      1 = Testing only           - Test FastReport rendering via API
      2 = Mapping + Testing      - Both operations sequentially

    \b
    QUICK START:
      1. Generate config:  odoo-fr-mapper --init
      2. Edit .env with your Odoo connection credentials
      3. Map all reports:  odoo-fr-mapper --yaml_path=./reports_yaml
      4. Map selected:     odoo-fr-mapper --yaml_path=./reports_yaml --select

    \b
    .ENV CONFIGURATION (required variables):
      ODOO_URL          Odoo server URL (e.g. https://odoo.example.com)
      ODOO_PORT         Server port (443 for HTTPS, 8069 for HTTP)
      ODOO_USER         Odoo username
      ODOO_PASSWORD     Odoo password
      ODOO_DATABASE     Database name
      ODOO_LANGUAGE     Locale code (de_DE, en_US, fr_FR; legacy: ger, eng)

    \b
    .ENV CONFIGURATION (optional variables):
      ODOO_WORKFLOW     0=mapping, 1=testing, 2=both (default: 0)
      ODOO_COLLECT_YAML Export reports FROM Odoo to YAML (default: False)
      ODOO_DISABLE_QWEB Disable QWeb reports after mapping (default: True)

    \b
    INTERACTIVE SELECTION (--select):
      Shows a table of all YAML files with filename, report name, and model.
      Enter comma-separated indices (e.g. 1,3,5) or 'all' to process.
      Without --select, all YAML files in the folder are processed.

    \b
    YAML COLLECTION MODE (ODOO_COLLECT_YAML=True):
      Exports existing FastReport entries from Odoo to YAML files.
      Shows interactive selection of available reports before export.
    """
    # Print banner
    print_banner()

    # Create connection from .env file
    try:
        connection, env_file_used = eq_utils.create_connection_from_env(env_path=env_path)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        click.echo("\n" + "=" * 80)
        click.echo("  Failed to load connection configuration")
        click.echo("  Run 'odoo-fr-mapper --init' to generate a .env template")
        if env_path:
            click.echo(f"  Searched in: {env_path}")
        else:
            click.echo(f"  Searched in: {os.getcwd()}")
        click.echo("=" * 80 + "\n")
        return

    # Show connection summary and ask for confirmation
    workflow_label = WORKFLOW_LABELS.get(connection.workflow, f"Unknown ({connection.workflow})")
    click.echo("  ┌─────────────────────────────────────────────────────────────────────┐")
    click.echo("  │  Connection Summary                                                 │")
    click.echo("  ├─────────────────────────────────────────────────────────────────────┤")
    click.echo(f"  │  .env:      {env_file_used:<55} │")
    click.echo(f"  │  Server:    {connection.url:<55} │")
    click.echo(f"  │  Port:      {str(connection.port):<55} │")
    click.echo(f"  │  Database:  {connection.database:<55} │")
    click.echo(f"  │  User:      {connection.username:<55} │")
    click.echo(f"  │  Workflow:  {workflow_label:<55} │")
    click.echo("  └─────────────────────────────────────────────────────────────────────┘")
    click.echo()

    if not click.confirm("  Proceed?", default=True):
        click.echo("\n  Aborted.")
        return

    # Login to Odoo
    connection.login()

    # Collect yaml
    if connection.collect_yaml:
        logger.info("Collecting YAML report entries...")

        # List available reports for interactive selection
        available_reports = connection.list_fast_reports()
        if not available_reports:
            click.echo("  No FastReport entries found in database.")
            return

        click.echo(f"\n  Found {len(available_reports)} FastReport(s):\n")
        click.echo(f"  {'#':>3}  {'Report Name':<40} {'Model':<25} {'Company':<20}")
        click.echo(f"  {'---':>3}  {'─' * 40} {'─' * 25} {'─' * 20}")
        for i, r in enumerate(available_reports, 1):
            click.echo(f"  {i:>3}  {r['report_name']:<40} {r['model']:<25} {r['company']:<20}")

        click.echo()
        selection = click.prompt(
            "  Select reports (e.g. 1,3,5 or 'all')",
            type=str,
            default="all",
        )

        if selection.strip().lower() == "all":
            selected_ids = [r["id"] for r in available_reports]
        else:
            try:
                indices = [int(x.strip()) for x in selection.split(",")]
                selected_ids = [available_reports[i - 1]["id"] for i in indices if 1 <= i <= len(available_reports)]
            except (ValueError, IndexError):
                click.echo("  Invalid selection. Aborting.")
                return

        if not selected_ids:
            click.echo("  No reports selected. Aborting.")
            return

        logger.info(f"Collecting {len(selected_ids)} selected report(s)...")
        connection.collect_report_entries(yaml_path, report_ids=selected_ids)
    # Yaml Mapping
    else:
        if select:
            report_items = eq_utils.list_yaml_reports(yaml_path)
            if not report_items:
                click.echo("  No YAML report files found.")
                return

            click.echo(f"\n  Found {len(report_items)} YAML report(s):\n")
            click.echo(f"  {'#':>3}  {'Filename':<40} {'Report Name':<35} {'Model':<25}")
            click.echo(f"  {'---':>3}  {'─' * 40} {'─' * 35} {'─' * 25}")
            for i, item in enumerate(report_items, 1):
                click.echo(f"  {i:>3}  {item['filename']:<40} {item['report_name']:<35} {item['model']:<25}")

            click.echo()
            selection = click.prompt(
                "  Select reports (e.g. 1,3,5 or 'all')",
                type=str,
                default="all",
            )

            if selection.strip().lower() == "all":
                selected_yamls = [item["yaml_object"] for item in report_items]
            else:
                try:
                    indices = [int(x.strip()) for x in selection.split(",")]
                    selected_yamls = [
                        report_items[i - 1]["yaml_object"] for i in indices if 1 <= i <= len(report_items)
                    ]
                except (ValueError, IndexError):
                    click.echo("  Invalid selection. Aborting.")
                    return

            if not selected_yamls:
                click.echo("  No reports selected. Aborting.")
                return

            logger.info(f"Processing {len(selected_yamls)} selected report(s)...")
            reports = eq_utils.build_reports_from_yaml_objects(selected_yamls)
        else:
            reports = eq_utils.collect_all_reports(yaml_path)

        failed_reports = []
        if connection.workflow == 0:
            logger.info("Starting report mapping...")
            failed_reports = connection.map_reports(reports)
        elif connection.workflow == 1:
            logger.info(f"Testing report rendering for database: {connection.database}")
            connection.test_fast_report_rendering(reports)
        elif connection.workflow == 2:
            logger.info("Starting report mapping...")
            failed_reports = connection.map_reports(reports)
            logger.info(f"Testing report rendering for database: {connection.database}")
            connection.test_fast_report_rendering(reports)
        else:
            logger.error("Invalid workflow configuration parameter value!")
            raise ValueError("Workflow must be 0 (mapping), 1 (testing), or 2 (both)")

        # Show summary if any reports failed
        if failed_reports:
            click.echo()
            click.echo(f"  ⚠ {len(failed_reports)} of {len(reports)} report(s) failed:")
            for name, error in failed_reports:
                # Truncate long error messages
                short_error = error[:80] + "..." if len(error) > 80 else error
                click.echo(f"    - {name}: {short_error}")
            click.echo()
            click.echo("  Tip: Re-run failed reports individually with:")
            click.echo(f"    odoo-fr-mapper --yaml_path={yaml_path} --select")
            click.echo()

    if connection.disable_qweb:
        logger.info("Disabling QWeb reports...")
        connection.disable_qweb_reports()

    logger.info("✅ Processing completed successfully!")
    click.echo("\n" + "=" * 80)
    click.echo("  ✅ All operations completed successfully!")
    click.echo("=" * 80 + "\n")


if __name__ == "__main__":
    start_odoo_fast_report_mapper()
