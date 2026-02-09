# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Comprehensive tests for odoo_report_helper.report.Report class.
"""

import pytest

from odoo_report_helper.report import Report

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_report():
    """Return a Report with only required arguments (all defaults)."""
    return Report(
        entry_name="test_entry",
        report_name="test_report",
        report_type="fast_report",
        model_name="sale.order",
    )


@pytest.fixture
def full_report():
    """Return a Report with all arguments explicitly set."""
    return Report(
        entry_name="custom_entry",
        report_name="custom_report",
        report_type="qweb-pdf",
        model_name="account.move",
        print_report_name="Invoice Report",
        attachment="Invoice.pdf",
        attachment_use=True,
        dependencies=["sale", "account"],
        model_fields={"account.move": ["id", "name"]},
        calculated_fields={"total": {"sum_func": ["amount"]}},
    )


# ---------------------------------------------------------------------------
# Constructor Tests
# ---------------------------------------------------------------------------


class TestReportConstructorDefaults:
    """Verify that default values are applied correctly."""

    def test_default_print_report_name(self, minimal_report):
        assert minimal_report.print_report_name == "Report"

    def test_default_attachment(self, minimal_report):
        assert minimal_report.attachment == "Report.pdf"

    def test_default_attachment_use(self, minimal_report):
        assert minimal_report.attachment_use is False

    def test_default_dependencies_is_empty_list(self, minimal_report):
        assert minimal_report._dependencies == []

    def test_default_model_fields_is_empty_dict(self, minimal_report):
        assert minimal_report._fields == {}

    def test_default_calculated_fields_is_empty_dict(self, minimal_report):
        assert minimal_report._calculated_fields == {}

    def test_default_data_dictionary_is_empty(self, minimal_report):
        assert minimal_report._data_dictionary == {}


class TestReportConstructorExplicit:
    """Verify that explicitly provided values are stored correctly."""

    def test_entry_name(self, full_report):
        assert full_report.entry_name == "custom_entry"

    def test_report_name(self, full_report):
        assert full_report.report_name == "custom_report"

    def test_report_type(self, full_report):
        assert full_report.report_type == "qweb-pdf"

    def test_model_name(self, full_report):
        assert full_report.model_name == "account.move"

    def test_print_report_name(self, full_report):
        assert full_report.print_report_name == "Invoice Report"

    def test_attachment(self, full_report):
        assert full_report.attachment == "Invoice.pdf"

    def test_attachment_use(self, full_report):
        assert full_report.attachment_use is True

    def test_dependencies(self, full_report):
        assert set(full_report._dependencies) == {"sale", "account"}

    def test_model_fields(self, full_report):
        assert full_report._fields == {"account.move": ["id", "name"]}

    def test_calculated_fields(self, full_report):
        assert full_report._calculated_fields == {"total": {"sum_func": ["amount"]}}


# ---------------------------------------------------------------------------
# Mutable Default Argument Safety
# ---------------------------------------------------------------------------


class TestMutableDefaultArguments:
    """Ensure that None-default mutable arguments are isolated between instances."""

    def test_dependencies_not_shared(self):
        r1 = Report("a", "r1", "fast_report", "res.partner")
        r2 = Report("b", "r2", "fast_report", "res.partner")
        r1._dependencies.append("sale")
        assert r2._dependencies == [], "Mutating r1 dependencies must not affect r2"

    def test_model_fields_not_shared(self):
        r1 = Report("a", "r1", "fast_report", "res.partner")
        r2 = Report("b", "r2", "fast_report", "res.partner")
        r1._fields["res.partner"] = ["id"]
        assert r2._fields == {}, "Mutating r1 fields must not affect r2"

    def test_calculated_fields_not_shared(self):
        r1 = Report("a", "r1", "fast_report", "res.partner")
        r2 = Report("b", "r2", "fast_report", "res.partner")
        r1._calculated_fields["total"] = {"fn": ["x"]}
        assert r2._calculated_fields == {}, "Mutating r1 calculated_fields must not affect r2"


# ---------------------------------------------------------------------------
# self_ensure
# ---------------------------------------------------------------------------


class TestSelfEnsure:
    """Verify that self_ensure populates _data_dictionary correctly."""

    def test_self_ensure_creates_correct_keys(self, minimal_report):
        minimal_report.self_ensure()
        expected_keys = {
            "name",
            "report_name",
            "report_type",
            "print_report_name",
            "model",
            "attachment",
            "attachment_use",
        }
        assert set(minimal_report._data_dictionary.keys()) == expected_keys

    def test_self_ensure_values_with_defaults(self, minimal_report):
        minimal_report.self_ensure()
        dd = minimal_report._data_dictionary
        assert dd["name"] == "test_entry"
        assert dd["report_name"] == "test_report"
        assert dd["report_type"] == "fast_report"
        assert dd["print_report_name"] == "Report"
        assert dd["model"] == "sale.order"
        assert dd["attachment"] == "Report.pdf"
        assert dd["attachment_use"] is False

    def test_self_ensure_values_with_explicit(self, full_report):
        full_report.self_ensure()
        dd = full_report._data_dictionary
        assert dd["name"] == "custom_entry"
        assert dd["report_name"] == "custom_report"
        assert dd["report_type"] == "qweb-pdf"
        assert dd["print_report_name"] == "Invoice Report"
        assert dd["model"] == "account.move"
        assert dd["attachment"] == "Invoice.pdf"
        assert dd["attachment_use"] is True

    def test_self_ensure_overwrites_previous(self, minimal_report):
        minimal_report.self_ensure()
        minimal_report.entry_name = "changed"
        minimal_report.self_ensure()
        assert minimal_report._data_dictionary["name"] == "changed"

    def test_self_ensure_does_not_include_fields(self, full_report):
        full_report.self_ensure()
        assert "fields" not in full_report._data_dictionary
        assert "calculated_fields" not in full_report._data_dictionary
        assert "dependencies" not in full_report._data_dictionary


# ---------------------------------------------------------------------------
# add_fields
# ---------------------------------------------------------------------------


class TestAddFields:
    """Verify add_fields merging and deduplication behavior."""

    def test_add_fields_single_model(self, minimal_report):
        minimal_report.add_fields({"sale.order": ["id", "name", "partner_id"]})
        assert "sale.order" in minimal_report._fields
        assert minimal_report._fields["sale.order"] == ["id", "name", "partner_id"]

    def test_add_fields_multiple_models(self, minimal_report):
        minimal_report.add_fields(
            {
                "sale.order": ["id", "name"],
                "res.partner": ["id", "email"],
            }
        )
        assert len(minimal_report._fields) == 2
        assert minimal_report._fields["sale.order"] == ["id", "name"]
        assert minimal_report._fields["res.partner"] == ["id", "email"]

    def test_add_fields_removes_duplicates(self, minimal_report):
        minimal_report.add_fields(
            {
                "sale.order": ["id", "name", "id", "name", "partner_id"],
            }
        )
        assert minimal_report._fields["sale.order"] == ["id", "name", "partner_id"]

    def test_add_fields_merges_with_existing(self):
        report = Report(
            entry_name="e",
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            model_fields={"sale.order": ["id"]},
        )
        report.add_fields({"res.partner": ["name"]})
        assert "sale.order" in report._fields
        assert "res.partner" in report._fields

    def test_add_fields_overwrites_existing_model_fields(self):
        report = Report(
            entry_name="e",
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            model_fields={"sale.order": ["id"]},
        )
        report.add_fields({"sale.order": ["name", "amount_total"]})
        assert report._fields["sale.order"] == ["name", "amount_total"]

    def test_add_fields_preserves_order(self, minimal_report):
        minimal_report.add_fields({"sale.order": ["z_field", "a_field", "m_field"]})
        assert minimal_report._fields["sale.order"] == ["z_field", "a_field", "m_field"]

    def test_add_fields_empty_dict(self, minimal_report):
        minimal_report.add_fields({})
        assert minimal_report._fields == {}


# ---------------------------------------------------------------------------
# add_calculated_fields
# ---------------------------------------------------------------------------


class TestAddCalculatedFields:
    """Verify add_calculated_fields behavior.

    NOTE: The method iterates ``field_dict`` directly (not .items()),
    so callers must pass an iterable of (key, value) tuples, such as
    the result of dict.items().
    """

    def test_add_calculated_fields_single(self, minimal_report):
        """After add_calculated_fields + self_clean, the inner dict is
        reduced to a list of its keys because self_clean applies
        list(dict.fromkeys(value)) on every value."""
        calc = {"payment_text": {"eq_get_payment_terms": ["partner_id.lang", "currency_id"]}}
        minimal_report.add_calculated_fields(calc.items())
        assert "payment_text" in minimal_report._calculated_fields
        # self_clean converts the inner dict to a list of its keys
        assert minimal_report._calculated_fields["payment_text"] == ["eq_get_payment_terms"]

    def test_add_calculated_fields_multiple(self, minimal_report):
        calc = {
            "field_a": {"func_a": ["p1"]},
            "field_b": {"func_b": ["p2", "p3"]},
        }
        minimal_report.add_calculated_fields(calc.items())
        assert len(minimal_report._calculated_fields) == 2
        assert "field_a" in minimal_report._calculated_fields
        assert "field_b" in minimal_report._calculated_fields

    def test_add_calculated_fields_merges_with_existing(self):
        report = Report(
            entry_name="e",
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            calculated_fields={"existing": {"fn": ["x"]}},
        )
        report.add_calculated_fields({"new_field": {"fn2": ["y"]}}.items())
        assert "existing" in report._calculated_fields
        assert "new_field" in report._calculated_fields


# ---------------------------------------------------------------------------
# add_dependencies
# ---------------------------------------------------------------------------


class TestAddDependencies:
    """Verify add_dependencies merging and deduplication behavior."""

    def test_add_dependencies_basic(self, minimal_report):
        minimal_report.add_dependencies(["sale", "account"])
        assert set(minimal_report._dependencies) == {"sale", "account"}

    def test_add_dependencies_removes_duplicates(self, minimal_report):
        minimal_report.add_dependencies(["sale", "sale", "account", "account"])
        assert sorted(minimal_report._dependencies) == ["account", "sale"]

    def test_add_dependencies_merges_with_existing(self):
        report = Report(
            entry_name="e",
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            dependencies=["base"],
        )
        report.add_dependencies(["sale", "account"])
        assert set(report._dependencies) == {"base", "sale", "account"}

    def test_add_dependencies_deduplicates_across_existing(self):
        report = Report(
            entry_name="e",
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            dependencies=["sale"],
        )
        report.add_dependencies(["sale", "account"])
        assert sorted(report._dependencies) == ["account", "sale"]

    def test_add_dependencies_empty_list(self, minimal_report):
        minimal_report.add_dependencies([])
        assert minimal_report._dependencies == []

    def test_add_dependencies_empty_list_preserves_existing(self):
        report = Report(
            entry_name="e",
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            dependencies=["sale"],
        )
        report.add_dependencies([])
        assert report._dependencies == ["sale"]

    def test_add_dependencies_called_multiple_times(self, minimal_report):
        minimal_report.add_dependencies(["sale"])
        minimal_report.add_dependencies(["account"])
        minimal_report.add_dependencies(["sale", "stock"])
        assert set(minimal_report._dependencies) == {"sale", "account", "stock"}
