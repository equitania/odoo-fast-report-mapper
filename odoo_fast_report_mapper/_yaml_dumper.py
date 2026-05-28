# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Custom YAML dumper with consistent indentation formatting."""

import yaml


class YAMLDumper(yaml.Dumper):
    """Custom YAML dumper for consistent indentation formatting."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)
