# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoorpc
import yaml
import os


def prepare_connection(url, port):
    """
        Build the OdooRPC connection object
        :param url: Odoo URL
        :param port: Port number
    """
    port = int(port)
    _protocol = 'jsonrpc+ssl'
    if url.startswith('https'):
        url = url.replace('https:', '')
        if port <= 0:
            port = 443

    elif url.startswith('http:'):
        url = url.replace('http:', '')
        _protocol = 'jsonrpc'

    while url and url.startswith('/'):
        url = url[1:]

    while url and url.endswith('/'):
        url = url[:-1]

    while url and url.endswith('\\'):
        url = url[:-1]

    connection = odoorpc.ODOO(url, port=port, protocol=_protocol)
    return connection


def fire_all_functions(function_list: list):
    """
        Execute each function in a list
        :param function_list: List of functions
    """
    for func in function_list:
        func()


def self_clean(input_dictionary: dict) -> dict:
    """
        Remove duplicates in dictionary
        :param: input_dictionary
        :return: return_dict
    """
    return_dict = input_dictionary.copy()
    for key, value in input_dictionary.items():
        return_dict[key] = list(dict.fromkeys(value))
    return return_dict


def parse_yaml(yaml_file):
    """
        Parse yaml file to object and return it
        :param: yaml_file: path to yaml file
        :return: yaml_object
    """
    with open(yaml_file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return False


def parse_yaml_folder(path):
    """
        Parse multiple yaml files to list of objects and return them
        :param: yaml_file: path to yaml files
        :return: yaml_objects
    """
    yaml_objects = []
    for file in os.listdir(path):
        if file.endswith(".yaml"):
            yaml_object = parse_yaml(os.path.join(path, file))
            if yaml_object:
                yaml_objects.append(yaml_object)
    return yaml_objects
