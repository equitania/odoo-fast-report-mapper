# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unittest
import odooreporthelper.utils as utils

# Enter your Odoo system parameters
url = "https://odoo.com/"
port = 443

test_yaml_object_1 = {'variable': 'var', 'dictionary': {'first': 'foo', 'second': 'bar'}, 'list': ['Hello', 'World'],
                      'nested_dictionary': {'nested_dictionary_1': {'nested_list_1': ['parameter1', 'parameter2']}}}
test_yaml_object_2 = {'variable': 'varo', 'dictionary': {'first': 'fooo', 'second': 'baro'},
                      'list': ['Helloo', 'Worldo'],
                      'nested_dictionary': {'nested_dictionary_1': {'nested_list_1': ['parameter1o', 'parameter2o']}}}


class UnitTestCase(unittest.TestCase):
    def test_prepare_connection(self):
        try:
            connection = utils.prepare_connection(url, port)
        except Exception as Ex:
            connection = None
        self.assertIsNotNone(connection)

    def test_self_clean(self):
        unclean_dict = {'foo': ['bar'], 'test3': ['123', '345', '123'], 'test2': [123], 'test': ['345', '345']}
        clean_dict = {'foo': ['bar'], 'test3': ['123', '345'], 'test2': [123], 'test': ['345']}
        result = utils.self_clean(unclean_dict)
        self.assertEqual(result, clean_dict)

    def test_parse_yaml(self):
        yaml_object = utils.parse_yaml("yaml_test/test.yaml")
        self.assertEqual(yaml_object, test_yaml_object_1)

    def test_parse_yaml_folder(self):
        list_of_yaml_objects = utils.parse_yaml_folder("yaml_test")
        self.assertEqual(list_of_yaml_objects, [test_yaml_object_1, test_yaml_object_2])


if __name__ == '__main__':
    unittest.main()
