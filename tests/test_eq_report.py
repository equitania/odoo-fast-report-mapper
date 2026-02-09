# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Comprehensive tests for EqReport class in odoo_fast_report_mapper/eq_report.py."""


from odoo_fast_report_mapper.eq_report import EqReport

# ---------------------------------------------------------------------------
# Helper: minimal required arguments for EqReport construction
# ---------------------------------------------------------------------------


def _make_report(**overrides):
    """Create an EqReport with sensible defaults, allowing per-test overrides."""
    defaults = {
        "entry_name": {"ger": "Verkaufsauftrag", "eng": "Sales_Order"},
        "report_name": "eq_fr_core_sale_order",
        "report_type": "fast_report",
        "model_name": "sale.order",
        "company_id": False,
    }
    defaults.update(overrides)
    return EqReport(**defaults)


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------


class TestEqReportConstructorDefaults:
    """Verify that default values are applied correctly."""

    def test_all_default_values(self):
        report = _make_report()

        assert report.entry_name == {"ger": "Verkaufsauftrag", "eng": "Sales_Order"}
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


class TestEqReportConstructorExplicit:
    """Verify that explicitly provided values override defaults."""

    def test_explicit_values(self, sample_report_yaml_data):
        data = sample_report_yaml_data
        report = EqReport(
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


# ---------------------------------------------------------------------------
# self_ensure() tests
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

    def test_name_uses_german_entry(self):
        """self_ensure() should use entry_name['ger'] for the 'name' key."""
        report = _make_report(entry_name={"ger": "Deutsche_Bezeichnung", "eng": "English_Name"})
        report.self_ensure()
        assert report._data_dictionary["name"] == "Deutsche_Bezeichnung"


# ---------------------------------------------------------------------------
# ensure_data_for_yaml() tests
# ---------------------------------------------------------------------------


class TestEnsureDataForYaml:
    """Tests for ensure_data_for_yaml which produces the YAML output dict."""

    def test_returns_correct_dict_without_company(self, sample_report_yaml_data):
        data = sample_report_yaml_data
        report = EqReport(
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

        # The first 5 keys should be: name, report_name, report_type,
        # print_report_name, report_model
        assert keys[5] == "company_id"
        assert keys[:5] == [
            "name",
            "report_name",
            "report_type",
            "print_report_name",
            "report_model",
        ]

    def test_yaml_data_uses_entry_name_dict_not_ger(self):
        """ensure_data_for_yaml() should store the full bilingual entry_name dict,
        not just the German string (which is what self_ensure() does)."""
        report = _make_report(entry_name={"ger": "Test_DE", "eng": "Test_EN"})
        result = report.ensure_data_for_yaml()
        assert result["name"] == {"ger": "Test_DE", "eng": "Test_EN"}

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
        report = EqReport(
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
