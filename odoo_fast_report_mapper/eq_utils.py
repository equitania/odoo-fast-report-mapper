# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import eq_report
from . import eq_odoo_connection
import odoo_report_helper.utils as utils
import odoo_report_helper.exceptions as exceptions
import copy
import os
from dotenv import load_dotenv
from .logging_config import get_logger

logger = get_logger(__name__)


def create_report_object_from_yaml_object(yaml_object):
    """
        Create EqReport object from yaml_object
        :param: yaml_object
        :return: EqReport object
    """
    # Set this in a try block because not all yaml files are up2date
    report = eq_report.EqReport(
        yaml_object['name'],
        yaml_object['report_name'],
        yaml_object['report_type'],
        yaml_object['report_model'],
        yaml_object.get('company_id', False),
        yaml_object['eq_export_type'],
        yaml_object['print_report_name'],
        yaml_object['attachment'],
        yaml_object['eq_ignore_images'],
        yaml_object['eq_handling_html_fields'],
        yaml_object['multi'],
        yaml_object['attachment_use'],
        yaml_object['eq_print_button'],
        yaml_object['dependencies'],
        yaml_object['report_fields'],
        yaml_object['calculated_fields'],
        yaml_object['eq_multiprint'],
    )
    return report


def create_odoo_connection_from_yaml_object(yaml_object):
    """
        Create EqOdooConnection object from yaml_object
        :param: yaml_object
        :return: EqOdooConnection object
    """
    eq_odoo_connection_object = eq_odoo_connection.EqOdooConnection(
        yaml_object['Server']['language'],
        yaml_object['Server']['collect_yaml'] if 'collect_yaml' in yaml_object['Server'] else False,
        yaml_object['Server']['disable_qweb'] if 'disable_qweb' in yaml_object['Server'] else True,
        yaml_object['Server']['workflow'] if 'workflow' in yaml_object['Server'] else 0,
        yaml_object['Server']['url'],
        yaml_object['Server']['port'],
        yaml_object['Server']['user'],
        yaml_object['Server']['password'],
        yaml_object['Server']['database'],
    )
    return eq_odoo_connection_object


def convert_all_yaml_objects(yaml_objects: list, converting_function):
    """
        Convert list of yaml_objects through a converting function
        :param: list of yaml_objects
        :param: Function with which the yaml_objects should be converted
        :return: list of objects
    """
    local_object_list = []
    for yaml_object in yaml_objects:
        local_object = converting_function(yaml_object)
        local_object_list.append(local_object)
    return local_object_list


def collect_all_reports(path):
    """
        Get all yaml objects from path and convert them into report objects
        :param: path to yaml files
        :return: list of report objects
    """
    try:
        yaml_report_objects = utils.parse_yaml_folder(path)
        filtered_yaml_report_objects = []
        for yaml_report_object in yaml_report_objects:
            if yaml_report_object.get('company_id') and len(yaml_report_object.get('company_id')) > 1:
                company_ids = yaml_report_object.get('company_id')
                del yaml_report_object['company_id']
                for company_id in company_ids:
                    temp_yaml_report_object = copy.deepcopy(yaml_report_object)
                    temp_yaml_report_object['company_id'] = [company_id]
                    filtered_yaml_report_objects.append(temp_yaml_report_object)
            else:
                filtered_yaml_report_objects.append(yaml_report_object)
        eq_report_objects = convert_all_yaml_objects(filtered_yaml_report_objects, create_report_object_from_yaml_object)
        return eq_report_objects
    except FileNotFoundError as ex:
        raise exceptions.PathDoesNotExitError("ERROR: Please check your Path" + " " + str(ex))
        sys.exit(0)


def create_connection_from_env(env_path=None):
    """
    Create EqOdooConnection object from environment variables (.env file).

    Args:
        env_path: Optional path to .env file. If None, searches in current directory.
                  Can be either a directory path or full path to .env file.

    Required environment variables:
        ODOO_URL: Odoo server URL (e.g., https://odoo.example.com)
        ODOO_PORT: Odoo server port (e.g., 443 for HTTPS, 8069 for HTTP)
        ODOO_USER: Odoo username
        ODOO_PASSWORD: Odoo password
        ODOO_DATABASE: Odoo database name
        ODOO_LANGUAGE: Language for report names ('ger' or 'eng')

    Optional environment variables:
        ODOO_COLLECT_YAML: Collect YAML from Odoo (default: False)
        ODOO_DISABLE_QWEB: Disable QWeb reports (default: True)
        ODOO_WORKFLOW: Workflow mode (0=mapping, 1=testing, 2=both, default: 0)

    :return: EqOdooConnection object
    :raises: ValueError if required environment variables are missing
    """
    # Determine .env file path
    if env_path:
        # If env_path is a directory, append .env filename
        if os.path.isdir(env_path):
            dotenv_path = os.path.join(env_path, '.env')
        else:
            dotenv_path = env_path

        if not os.path.exists(dotenv_path):
            logger.error(f".env file not found at: {dotenv_path}")
            raise ValueError(f".env file not found at: {dotenv_path}")

        logger.info(f"Loading .env from: {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path)
    else:
        # Load .env file from current directory
        load_dotenv()

    # Required variables
    required_vars = {
        'ODOO_URL': 'url',
        'ODOO_PORT': 'port',
        'ODOO_USER': 'user',
        'ODOO_PASSWORD': 'password',
        'ODOO_DATABASE': 'database',
        'ODOO_LANGUAGE': 'language'
    }

    # Check for missing required variables
    missing_vars = [var for var in required_vars.keys() if not os.getenv(var)]
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        logger.info("Please create a .env file based on .env.example")
        raise ValueError(error_msg)

    # Get required values
    url = os.getenv('ODOO_URL')
    port = int(os.getenv('ODOO_PORT'))
    user = os.getenv('ODOO_USER')
    password = os.getenv('ODOO_PASSWORD')
    database = os.getenv('ODOO_DATABASE')
    language = os.getenv('ODOO_LANGUAGE')

    # Get optional values with defaults
    collect_yaml = os.getenv('ODOO_COLLECT_YAML', 'False').lower() in ('true', '1', 'yes')
    disable_qweb = os.getenv('ODOO_DISABLE_QWEB', 'True').lower() in ('true', '1', 'yes')
    workflow = int(os.getenv('ODOO_WORKFLOW', '0'))

    logger.info(f"Creating connection to {database}@{url}:{port}")
    logger.debug(f"Configuration: language={language}, workflow={workflow}, collect_yaml={collect_yaml}, disable_qweb={disable_qweb}")

    # Create connection object
    # EqOdooConnection expects: language, collect_yaml, disable_qweb, workflow, url, port, username, password, database
    connection = eq_odoo_connection.EqOdooConnection(
        language,
        collect_yaml,
        disable_qweb,
        workflow,
        url,
        port,
        user,  # Will be passed as 'username' to parent class
        password,
        database
    )

    return connection


def collect_all_connections(path):
    """
    DEPRECATED: Get all yaml objects from path and convert them into connection objects.

    This function is deprecated and maintained only for backwards compatibility.
    Use create_connection_from_env() instead for better security.

    :param: path to yaml files
    :return: list of connection objects
    """
    logger.warning("collect_all_connections() is deprecated. Use create_connection_from_env() instead.")
    try:
        yaml_connection_objects = utils.parse_yaml_folder(path)
        eq_connection_objects = convert_all_yaml_objects(yaml_connection_objects,
                                                         create_odoo_connection_from_yaml_object)
        return eq_connection_objects
    except FileNotFoundError as ex:
        raise exceptions.PathDoesNotExitError("ERROR: Please check your Path" + " " + str(ex))
        sys.exit(0)
