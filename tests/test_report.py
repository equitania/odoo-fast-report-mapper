# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Comprehensive tests for Report class in odoo_fast_report_mapper/_report.py."""

import pytest

from odoo_fast_report_mapper._report import Report

# ---------------------------------------------------------------------------
# Helper: minimal required arguments for Report construction
# ---------------------------------------------------------------------------


def _make_report(**overrides):
    """Create a Report with sensible defaults, allowing per-test overrides."""
    defaults = {
        "entry_name": {"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"},
        "report_name": "eq_fr_core_sale_order",
        "report_type": "fast_report",
        "model_name": "sale.order",
        "company_id": False,
    }
    defaults.update(overrides)
    return Report(**defaults)


# ---------------------------------------------------------------------------
# Base fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_report():
    """Return a Report with required arguments.

    Uses dependencies=[] (not False) so that add_dependencies works correctly.
    """
    return Report(
        entry_name={"de_DE": "test_entry"},
        report_name="test_report",
        report_type="fast_report",
        model_name="sale.order",
        company_id=False,
        dependencies=[],
    )


@pytest.fixture
def full_report():
    """Return a Report with all arguments explicitly set."""
    return Report(
        entry_name={"de_DE": "custom_entry", "en_US": "custom_entry"},
        report_name="custom_report",
        report_type="qweb-pdf",
        model_name="account.move",
        company_id=False,
        print_report_name="Invoice Report",
        attachment="Invoice.pdf",
        attachment_use=True,
        dependencies=["sale", "account"],
        model_fields={"account.move": ["id", "name"]},
        calculated_fields={"total": {"sum_func": ["amount"]}},
    )


# ---------------------------------------------------------------------------
# Constructor tests (EqReport-style — dict entry_name)
# ---------------------------------------------------------------------------


class TestReportConstructorDefaults:
    """Verify that default values are applied correctly."""

    def test_all_default_values(self):
        report = _make_report()

        assert report.entry_name == {"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"}
        assert report.report_name == "eq_fr_core_sale_order"
        assert report.report_type == "fast_report"
        assert report.model_name == "sale.order"
        assert report.company_id is False
        assert report.eq_export_type == "pdf"
        assert report.print_report_name == "Report"
        assert report.attachment == "Report.pdf"
        assert report.eq_ignore_images is True
        assert report.eq_handling_html_fields == "standard"
        assert report.multi is False
        assert report.attachment_use is False
        assert report.eq_print_button is False
        assert report._dependencies is False
        assert report._fields == {}
        assert report._calculated_fields == {}
        assert report.eq_multiprint == "standard"
        assert report._data_dictionary == {}

    def test_mutable_default_fields_are_independent(self):
        """Ensure each instance gets its own mutable containers."""
        r1 = _make_report()
        r2 = _make_report()
        r1._fields["sale.order"] = ["id"]
        assert r2._fields == {}

    def test_mutable_default_calculated_fields_are_independent(self):
        r1 = _make_report()
        r2 = _make_report()
        r1._calculated_fields["test"] = {"fn": ["a"]}
        assert r2._calculated_fields == {}

    def test_default_print_report_name(self, minimal_report):
        assert minimal_report.print_report_name == "Report"

    def test_default_attachment(self, minimal_report):
        assert minimal_report.attachment == "Report.pdf"

    def test_default_attachment_use(self, minimal_report):
        assert minimal_report.attachment_use is False

    def test_default_dependencies_is_false_for_eq_style(self):
        """EqReport-style: no deps defaults to False."""
        report = _make_report()
        assert report._dependencies is False

    def test_default_model_fields_is_empty_dict(self, minimal_report):
        assert minimal_report._fields == {}

    def test_default_calculated_fields_is_empty_dict(self, minimal_report):
        assert minimal_report._calculated_fields == {}

    def test_default_data_dictionary_is_empty(self, minimal_report):
        assert minimal_report._data_dictionary == {}


class TestReportConstructorExplicit:
    """Verify that explicitly provided values override defaults."""

    def test_explicit_values(self, sample_report_yaml_data):
        data = sample_report_yaml_data
        report = Report(
            entry_name=data["name"],
            report_name=data["report_name"],
            report_type=data["report_type"],
            model_name=data["report_model"],
            company_id=False,
            eq_export_type=data["eq_export_type"],
            print_report_name=data["print_report_name"],
            attachment=data["attachment"],
            eq_ignore_images=data["eq_ignore_images"],
            eq_handling_html_fields=data["eq_handling_html_fields"],
            multi=data["multi"],
            attachment_use=data["attachment_use"],
            eq_print_button=data["eq_print_button"],
            dependencies=data["dependencies"],
            model_fields=data["report_fields"],
            calculated_fields=data["calculated_fields"],
            eq_multiprint=data["eq_multiprint"],
        )

        assert report.entry_name == data["name"]
        assert report.report_name == data["report_name"]
        assert report.report_type == data["report_type"]
        assert report.model_name == data["report_model"]
        assert report.eq_export_type == data["eq_export_type"]
        assert report.print_report_name == data["print_report_name"]
        assert report.attachment == data["attachment"]
        assert report.eq_ignore_images is True
        assert report.eq_handling_html_fields == "standard"
        assert report.multi is False
        assert report.attachment_use is False
        assert report.eq_print_button is False
        assert report._dependencies == ["sale", "account"]
        assert report._fields == data["report_fields"]
        assert report._calculated_fields == data["calculated_fields"]
        assert report.eq_multiprint == "standard"

    def test_non_default_export_type(self):
        report = _make_report(eq_export_type="xlsx")
        assert report.eq_export_type == "xlsx"

    def test_company_id_as_list(self):
        report = _make_report(company_id=[1, 3])
        assert report.company_id == [1, 3]

    def test_entry_name_dict(self, full_report):
        assert full_report.entry_name == {"de_DE": "custom_entry", "en_US": "custom_entry"}

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
        r1 = Report({"de_DE": "a"}, "r1", "fast_report", "res.partner", False)
        r2 = Report({"de_DE": "b"}, "r2", "fast_report", "res.partner", False)
        if r1._dependencies:
            r1._dependencies.append("sale")
        assert r2._dependencies == [] or r2._dependencies is False

    def test_model_fields_not_shared(self):
        r1 = Report({"de_DE": "a"}, "r1", "fast_report", "res.partner", False)
        r2 = Report({"de_DE": "b"}, "r2", "fast_report", "res.partner", False)
        r1._fields["res.partner"] = ["id"]
        assert r2._fields == {}

    def test_calculated_fields_not_shared(self):
        r1 = Report({"de_DE": "a"}, "r1", "fast_report", "res.partner", False)
        r2 = Report({"de_DE": "b"}, "r2", "fast_report", "res.partner", False)
        r1._calculated_fields["total"] = {"fn": ["x"]}
        assert r2._calculated_fields == {}


# ---------------------------------------------------------------------------
# self_ensure() tests — EqReport style (dict entry_name)
# ---------------------------------------------------------------------------


class TestSelfEnsure:
    """Tests for the self_ensure method that builds _data_dictionary."""

    def test_creates_correct_data_dictionary(self):
        report = _make_report()
        report.self_ensure()

        expected_keys = {
            "name",
            "report_name",
            "report_type",
            "print_report_name",
            "model",
            "company_id",
            "eq_export_type",
            "eq_ignore_images",
            "eq_handling_html_fields",
            "eq_multiprint",
            "multi",
            "attachment",
            "attachment_use",
            "eq_print_button",
        }
        assert set(report._data_dictionary.keys()) == expected_keys

    def test_values_match_attributes(self):
        report = _make_report(
            eq_export_type="png",
            eq_ignore_images=False,
            multi=True,
        )
        report.self_ensure()

        assert report._data_dictionary["name"] == "Verkaufsauftrag"
        assert report._data_dictionary["report_name"] == "eq_fr_core_sale_order"
        assert report._data_dictionary["report_type"] == "fast_report"
        assert report._data_dictionary["print_report_name"] == "Report"
        assert report._data_dictionary["model"] == "sale.order"
        assert report._data_dictionary["eq_export_type"] == "png"
        assert report._data_dictionary["eq_ignore_images"] is False
        assert report._data_dictionary["multi"] is True

    def test_with_company_id_sets_first_element(self):
        """When company_id is a list, _data_dictionary should contain company_id[0]."""
        report = _make_report(company_id=[5, 10])
        report.self_ensure()
        assert report._data_dictionary["company_id"] == 5

    def test_without_company_id_sets_false(self):
        """When company_id is falsy, _data_dictionary should contain False."""
        report = _make_report(company_id=False)
        report.self_ensure()
        assert report._data_dictionary["company_id"] is False

    def test_with_empty_list_company_id_sets_false(self):
        """An empty list is falsy, so company_id should be False."""
        report = _make_report(company_id=[])
        report.self_ensure()
        assert report._data_dictionary["company_id"] is False

    def test_name_uses_primary_lang_entry(self):
        """self_ensure() should use primary language (de_DE) for the 'name' key."""
        report = _make_report(entry_name={"de_DE": "Deutsche_Bezeichnung", "en_US": "English_Name"})
        report.self_ensure()
        assert report._data_dictionary["name"] == "Deutsche_Bezeichnung"

    def test_name_uses_de_CH_as_fallback(self):
        """self_ensure() should use de_CH when de_DE is not present."""
        report = _make_report(entry_name={"de_CH": "Schweizer_Name", "en_US": "English_Name"})
        report.self_ensure()
        assert report._data_dictionary["name"] == "Schweizer_Name"

    def test_name_uses_first_key_when_no_german(self):
        """self_ensure() should use first key when no German variant exists."""
        report = _make_report(entry_name={"en_US": "English_Name", "fr_FR": "French_Name"})
        report.self_ensure()
        assert report._data_dictionary["name"] == "English_Name"

    def test_self_ensure_creates_correct_keys_base(self):
        """The merged Report always uses the full EqReport-style _data_dictionary."""
        report = Report(
            entry_name={"de_DE": "Test", "en_US": "Test"},
            report_name="test_report",
            report_type="fast_report",
            model_name="sale.order",
            company_id=False,
            dependencies=[],
        )
        report.self_ensure()
        dd = report._data_dictionary
        assert "name" in dd
        assert "report_name" in dd
        assert "report_type" in dd
        assert "print_report_name" in dd
        assert "model" in dd
        assert "attachment" in dd
        assert "attachment_use" in dd

    def test_self_ensure_values_with_defaults_base(self):
        report = Report(
            entry_name={"de_DE": "test_entry", "en_US": "test_entry"},
            report_name="test_report",
            report_type="fast_report",
            model_name="sale.order",
            company_id=False,
            dependencies=[],
        )
        report.self_ensure()
        dd = report._data_dictionary
        assert dd["name"] == "test_entry"
        assert dd["report_name"] == "test_report"
        assert dd["report_type"] == "fast_report"
        assert dd["print_report_name"] == "Report"
        assert dd["model"] == "sale.order"
        assert dd["attachment"] == "Report.pdf"
        assert dd["attachment_use"] is False

    def test_self_ensure_overwrites_previous(self):
        report = Report(
            entry_name={"de_DE": "original", "en_US": "original"},
            report_name="test_report",
            report_type="fast_report",
            model_name="sale.order",
            company_id=False,
            dependencies=[],
        )
        report.self_ensure()
        report.entry_name = {"de_DE": "changed", "en_US": "changed"}
        report.self_ensure()
        assert report._data_dictionary["name"] == "changed"

    def test_self_ensure_does_not_include_fields(self):
        """self_ensure should not include fields, calculated_fields, or dependencies."""
        report = Report(
            entry_name={"de_DE": "Test", "en_US": "Test"},
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            company_id=False,
            dependencies=["sale", "account"],
            model_fields={"sale.order": ["id", "name"]},
            calculated_fields={"total": {"sum_func": ["amount"]}},
        )
        report.self_ensure()
        assert "fields" not in report._data_dictionary
        assert "calculated_fields" not in report._data_dictionary
        assert "dependencies" not in report._data_dictionary


# ---------------------------------------------------------------------------
# ensure_data_for_yaml() tests
# ---------------------------------------------------------------------------


class TestEnsureDataForYaml:
    """Tests for ensure_data_for_yaml which produces the YAML output dict."""

    def test_returns_correct_dict_without_company(self, sample_report_yaml_data):
        data = sample_report_yaml_data
        report = Report(
            entry_name=data["name"],
            report_name=data["report_name"],
            report_type=data["report_type"],
            model_name=data["report_model"],
            company_id=False,
            eq_export_type=data["eq_export_type"],
            print_report_name=data["print_report_name"],
            attachment=data["attachment"],
            eq_ignore_images=data["eq_ignore_images"],
            eq_handling_html_fields=data["eq_handling_html_fields"],
            multi=data["multi"],
            attachment_use=data["attachment_use"],
            eq_print_button=data["eq_print_button"],
            dependencies=data["dependencies"],
            model_fields=data["report_fields"],
            calculated_fields=data["calculated_fields"],
            eq_multiprint=data["eq_multiprint"],
        )
        result = report.ensure_data_for_yaml()

        assert result["name"] == data["name"]
        assert result["report_name"] == data["report_name"]
        assert result["report_type"] == data["report_type"]
        assert result["print_report_name"] == data["print_report_name"]
        assert result["report_model"] == data["report_model"]
        assert result["eq_export_type"] == data["eq_export_type"]
        assert result["dependencies"] == data["dependencies"]
        assert result["report_fields"] == data["report_fields"]
        assert result["calculated_fields"] == data["calculated_fields"]

    def test_no_company_id_key_when_falsy(self):
        """When company_id is falsy, the returned dict must NOT contain 'company_id'."""
        report = _make_report(company_id=False)
        result = report.ensure_data_for_yaml()
        assert "company_id" not in result

    def test_company_id_inserted_when_present(self):
        """When company_id is truthy, it must appear in the returned dict."""
        report = _make_report(company_id=[1, 3])
        result = report.ensure_data_for_yaml()
        assert "company_id" in result
        assert result["company_id"] == [1, 3]

    def test_company_id_inserted_at_position_5(self):
        """company_id should be inserted after the first 5 keys (index 5)."""
        report = _make_report(company_id=[2, 7])
        result = report.ensure_data_for_yaml()
        keys = list(result.keys())

        assert keys[5] == "company_id"
        assert keys[:5] == [
            "name",
            "report_name",
            "report_type",
            "print_report_name",
            "report_model",
        ]

    def test_yaml_data_uses_entry_name_dict_not_single_value(self):
        """ensure_data_for_yaml() should store the full multilingual entry_name dict."""
        report = _make_report(entry_name={"de_DE": "Test_DE", "en_US": "Test_EN"})
        result = report.ensure_data_for_yaml()
        assert result["name"] == {"de_DE": "Test_DE", "en_US": "Test_EN"}

    def test_yaml_data_key_order_without_company(self):
        """Verify the full key ordering when company_id is absent."""
        report = _make_report(company_id=False)
        result = report.ensure_data_for_yaml()
        expected_keys = [
            "name",
            "report_name",
            "report_type",
            "print_report_name",
            "report_model",
            "eq_export_type",
            "eq_ignore_images",
            "eq_handling_html_fields",
            "eq_multiprint",
            "multi",
            "attachment",
            "attachment_use",
            "eq_print_button",
            "dependencies",
            "report_fields",
            "calculated_fields",
        ]
        assert list(result.keys()) == expected_keys

    def test_matches_sample_fixture_with_company(self, sample_report_yaml_data_with_company):
        """Cross-check against the conftest fixture that includes company_id."""
        data = sample_report_yaml_data_with_company
        report = Report(
            entry_name=data["name"],
            report_name=data["report_name"],
            report_type=data["report_type"],
            model_name=data["report_model"],
            company_id=data["company_id"],
            eq_export_type=data["eq_export_type"],
            print_report_name=data["print_report_name"],
            attachment=data["attachment"],
            eq_ignore_images=data["eq_ignore_images"],
            eq_handling_html_fields=data["eq_handling_html_fields"],
            multi=data["multi"],
            attachment_use=data["attachment_use"],
            eq_print_button=data["eq_print_button"],
            dependencies=data["dependencies"],
            model_fields=data["report_fields"],
            calculated_fields=data["calculated_fields"],
            eq_multiprint=data["eq_multiprint"],
        )
        result = report.ensure_data_for_yaml()

        assert result["company_id"] == [1, 3]
        assert list(result.keys())[5] == "company_id"
        assert result["report_model"] == "account.move"
        assert result["dependencies"] == ["account"]


# ---------------------------------------------------------------------------
# add_fields tests
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
            entry_name={"de_DE": "e"},
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            company_id=False,
            model_fields={"sale.order": ["id"]},
        )
        report.add_fields({"res.partner": ["name"]})
        assert "sale.order" in report._fields
        assert "res.partner" in report._fields

    def test_add_fields_overwrites_existing_model_fields(self):
        report = Report(
            entry_name={"de_DE": "e"},
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            company_id=False,
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
# add_calculated_fields tests
# ---------------------------------------------------------------------------


class TestAddCalculatedFields:
    """Verify add_calculated_fields behavior."""

    def test_calculated_fields_parameter_list_preserved(self):
        """BUG-02 regression: parameter lists must survive add_calculated_fields intact.

        self_clean() on a dict iterates over keys only, so
        {"eq_get_payment_terms": ["p1","p2"]} would become ["eq_get_payment_terms"].
        The fix removes the broken self_clean call from add_calculated_fields.
        """
        report = _make_report()
        report.add_calculated_fields({"payment_text": {"eq_get_payment_terms": ["partner_id.lang", "currency_id"]}})
        assert report._calculated_fields["payment_text"] == {"eq_get_payment_terms": ["partner_id.lang", "currency_id"]}

    def test_add_calculated_fields_single(self, minimal_report):
        """Parameter lists inside calculated field dicts must be preserved intact."""
        calc = {"payment_text": {"eq_get_payment_terms": ["partner_id.lang", "currency_id"]}}
        minimal_report.add_calculated_fields(calc)
        assert "payment_text" in minimal_report._calculated_fields
        # Inner dict must be preserved as-is — values are {function_name: [params]}, not lists
        assert minimal_report._calculated_fields["payment_text"] == {
            "eq_get_payment_terms": ["partner_id.lang", "currency_id"]
        }

    def test_add_calculated_fields_multiple(self, minimal_report):
        calc = {
            "field_a": {"func_a": ["p1"]},
            "field_b": {"func_b": ["p2", "p3"]},
        }
        minimal_report.add_calculated_fields(calc)
        assert len(minimal_report._calculated_fields) == 2
        assert "field_a" in minimal_report._calculated_fields
        assert "field_b" in minimal_report._calculated_fields

    def test_add_calculated_fields_merges_with_existing(self):
        report = Report(
            entry_name={"de_DE": "e"},
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            company_id=False,
            calculated_fields={"existing": {"fn": ["x"]}},
        )
        report.add_calculated_fields({"new_field": {"fn2": ["y"]}})
        assert "existing" in report._calculated_fields
        assert "new_field" in report._calculated_fields


# ---------------------------------------------------------------------------
# add_dependencies tests
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
            entry_name={"de_DE": "e"},
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            company_id=False,
            dependencies=["base"],
        )
        report.add_dependencies(["sale", "account"])
        assert set(report._dependencies) == {"base", "sale", "account"}

    def test_add_dependencies_deduplicates_across_existing(self):
        report = Report(
            entry_name={"de_DE": "e"},
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            company_id=False,
            dependencies=["sale"],
        )
        report.add_dependencies(["sale", "account"])
        assert sorted(report._dependencies) == ["account", "sale"]

    def test_add_dependencies_empty_list(self, minimal_report):
        minimal_report.add_dependencies([])
        assert minimal_report._dependencies == []

    def test_add_dependencies_empty_list_preserves_existing(self):
        report = Report(
            entry_name={"de_DE": "e"},
            report_name="r",
            report_type="fast_report",
            model_name="sale.order",
            company_id=False,
            dependencies=["sale"],
        )
        report.add_dependencies([])
        assert report._dependencies == ["sale"]

    def test_add_dependencies_called_multiple_times(self, minimal_report):
        minimal_report.add_dependencies(["sale"])
        minimal_report.add_dependencies(["account"])
        minimal_report.add_dependencies(["sale", "stock"])
        assert set(minimal_report._dependencies) == {"sale", "account", "stock"}


# ---------------------------------------------------------------------------
# BUG-06 regression: entry_name isinstance guard
# ---------------------------------------------------------------------------


class TestReportEntryNameGuard:
    """Regression tests for BUG-06: entry_name must be a non-empty dict."""

    _required_kwargs = {
        "report_name": "eq_fr_test",
        "report_type": "fast_report",
        "model_name": "sale.order",
        "company_id": False,
    }

    def test_string_entry_name_raises_type_error(self):
        """Passing a plain string must raise TypeError with informative message."""
        with pytest.raises(TypeError, match="entry_name must be a non-empty dict"):
            Report(entry_name="not_a_dict", **self._required_kwargs)

    def test_empty_dict_entry_name_raises_type_error(self):
        """Passing an empty dict must raise TypeError (non-empty guard)."""
        with pytest.raises(TypeError, match="entry_name must be a non-empty dict"):
            Report(entry_name={}, **self._required_kwargs)

    def test_valid_dict_entry_name_accepted(self):
        """A non-empty dict must be accepted and stored as-is."""
        report = Report(entry_name={"de_DE": "Test"}, **self._required_kwargs)
        assert report.entry_name == {"de_DE": "Test"}
