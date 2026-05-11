# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Tests for odoo_fast_report_mapper/lang_utils.py - Language utility functions."""

from odoo_fast_report_mapper.lang_utils import (
    LEGACY_LANG_MAP,
    build_name_search_domain,
    get_primary_lang,
    normalize_language_code,
    normalize_name_dict,
    resolve_attachment_value,
)

# ---------------------------------------------------------------------------
# normalize_language_code() tests
# ---------------------------------------------------------------------------


class TestNormalizeLanguageCode:
    """Verify legacy-to-locale code conversion."""

    def test_ger_to_de_DE(self):
        assert normalize_language_code("ger") == "de_DE"

    def test_eng_to_en_US(self):
        assert normalize_language_code("eng") == "en_US"

    def test_de_DE_passthrough(self):
        assert normalize_language_code("de_DE") == "de_DE"

    def test_en_US_passthrough(self):
        assert normalize_language_code("en_US") == "en_US"

    def test_fr_FR_passthrough(self):
        assert normalize_language_code("fr_FR") == "fr_FR"

    def test_de_CH_passthrough(self):
        assert normalize_language_code("de_CH") == "de_CH"

    def test_unknown_code_passthrough(self):
        assert normalize_language_code("ja_JP") == "ja_JP"


# ---------------------------------------------------------------------------
# normalize_name_dict() tests
# ---------------------------------------------------------------------------


class TestNormalizeNameDict:
    """Verify name dict key normalization."""

    def test_legacy_dict_normalized(self):
        result = normalize_name_dict({"ger": "Verkauf", "eng": "Sales"})
        assert result == {"de_DE": "Verkauf", "en_US": "Sales"}

    def test_modern_dict_passthrough(self):
        result = normalize_name_dict({"de_DE": "Verkauf", "en_US": "Sales"})
        assert result == {"de_DE": "Verkauf", "en_US": "Sales"}

    def test_mixed_dict(self):
        result = normalize_name_dict({"ger": "Verkauf", "fr_FR": "Ventes"})
        assert result == {"de_DE": "Verkauf", "fr_FR": "Ventes"}

    def test_multi_language_dict(self):
        result = normalize_name_dict(
            {
                "de_DE": "Verkauf",
                "en_US": "Sales",
                "fr_FR": "Ventes",
                "de_CH": "Verkauf_CH",
            }
        )
        assert result == {
            "de_DE": "Verkauf",
            "en_US": "Sales",
            "fr_FR": "Ventes",
            "de_CH": "Verkauf_CH",
        }

    def test_single_language(self):
        result = normalize_name_dict({"ger": "Test"})
        assert result == {"de_DE": "Test"}

    def test_empty_dict(self):
        result = normalize_name_dict({})
        assert result == {}


# ---------------------------------------------------------------------------
# get_primary_lang() tests
# ---------------------------------------------------------------------------


class TestGetPrimaryLang:
    """Verify primary language selection priority."""

    def test_de_DE_is_primary(self):
        assert get_primary_lang({"de_DE": "A", "en_US": "B"}) == "de_DE"

    def test_de_CH_fallback(self):
        assert get_primary_lang({"de_CH": "A", "en_US": "B"}) == "de_CH"

    def test_de_AT_fallback(self):
        assert get_primary_lang({"de_AT": "A", "en_US": "B", "fr_FR": "C"}) == "de_AT"

    def test_de_DE_preferred_over_de_CH(self):
        assert get_primary_lang({"de_CH": "A", "de_DE": "B", "en_US": "C"}) == "de_DE"

    def test_non_german_returns_first_key(self):
        assert get_primary_lang({"en_US": "A", "fr_FR": "B"}) == "en_US"

    def test_single_language(self):
        assert get_primary_lang({"fr_FR": "Test"}) == "fr_FR"

    def test_legacy_ger_key(self):
        """After normalization ger becomes de_DE, but if raw legacy dict is passed."""
        assert get_primary_lang({"ger": "A", "eng": "B"}) == "ger"


# ---------------------------------------------------------------------------
# build_name_search_domain() tests
# ---------------------------------------------------------------------------


class TestBuildNameSearchDomain:
    """Verify Odoo search domain construction."""

    def test_single_name(self):
        result = build_name_search_domain({"de_DE": "Verkauf"})
        assert result == [
            "|",
            ("name", "=ilike", "Verkauf"),
            ("name", "=ilike", "Verkauf (PDF)"),
        ]

    def test_two_names(self):
        result = build_name_search_domain({"de_DE": "Verkauf", "en_US": "Sales"})
        # 4 conditions -> 3 OR operators
        assert result.count("|") == 3
        assert ("name", "=ilike", "Verkauf") in result
        assert ("name", "=ilike", "Verkauf (PDF)") in result
        assert ("name", "=ilike", "Sales") in result
        assert ("name", "=ilike", "Sales (PDF)") in result

    def test_three_names(self):
        result = build_name_search_domain(
            {
                "de_DE": "Verkauf",
                "en_US": "Sales",
                "fr_FR": "Ventes",
            }
        )
        # 6 conditions -> 5 OR operators
        assert result.count("|") == 5
        assert ("name", "=ilike", "Ventes") in result
        assert ("name", "=ilike", "Ventes (PDF)") in result

    def test_empty_dict(self):
        result = build_name_search_domain({})
        assert result == []

    def test_domain_structure_is_valid_odoo_format(self):
        """Verify the domain structure follows Odoo's prefix notation."""
        result = build_name_search_domain({"de_DE": "A", "en_US": "B"})
        # All '|' operators must come before the tuples
        or_count = 0
        for item in result:
            if item == "|":
                or_count += 1
            else:
                break
        tuples = [item for item in result if isinstance(item, tuple)]
        assert or_count == len(tuples) - 1


# ---------------------------------------------------------------------------
# Mapping constants tests
# ---------------------------------------------------------------------------


class TestMappingConstants:
    """Verify mapping constant correctness."""

    def test_legacy_lang_map(self):
        assert LEGACY_LANG_MAP == {"ger": "de_DE", "eng": "en_US"}


# ---------------------------------------------------------------------------
# resolve_attachment_value() tests
# ---------------------------------------------------------------------------


class TestResolveAttachmentValue:
    """Verify attachment dict resolution to single string value."""

    def test_string_passthrough(self):
        """String attachment passes through unchanged (backward compatibility)."""
        assert resolve_attachment_value("Report.pdf", "de_DE") == "Report.pdf"

    def test_none_passthrough(self):
        """None/falsy attachment passes through unchanged."""
        assert resolve_attachment_value(None, "de_DE") is None
        assert resolve_attachment_value("", "de_DE") == ""
        assert resolve_attachment_value(False, "de_DE") is False

    def test_dict_company_lang_match(self):
        """Dict attachment resolves to company_lang when present."""
        attachment = {"de_DE": "Angebot.pdf", "en_US": "Quotation.pdf"}
        assert resolve_attachment_value(attachment, "de_DE") == "Angebot.pdf"

    def test_dict_company_lang_en_US(self):
        """Dict attachment resolves to en_US when company speaks English."""
        attachment = {"de_DE": "Angebot.pdf", "en_US": "Quotation.pdf"}
        assert resolve_attachment_value(attachment, "en_US") == "Quotation.pdf"

    def test_dict_fallback_lang(self):
        """Dict attachment falls back to fallback_lang when company_lang not in dict."""
        attachment = {"de_DE": "Angebot.pdf", "en_US": "Quotation.pdf"}
        assert resolve_attachment_value(attachment, "fr_FR", fallback_lang="en_US") == "Quotation.pdf"

    def test_dict_primary_lang_fallback(self):
        """Dict attachment falls back to primary_lang (de_DE priority) when no match."""
        attachment = {"de_DE": "Angebot.pdf", "en_US": "Quotation.pdf"}
        assert resolve_attachment_value(attachment, "fr_FR") == "Angebot.pdf"

    def test_dict_first_value_fallback(self):
        """Dict attachment falls back to first value when nothing else matches."""
        attachment = {"fr_FR": "Devis.pdf", "it_IT": "Preventivo.pdf"}
        assert resolve_attachment_value(attachment, "ja_JP") == "Devis.pdf"

    def test_complex_odoo_expression(self):
        """Dict attachment with complex Odoo conditional expressions."""
        attachment = {
            "de_DE": "(object.state in ('draft','sent')) and ('Angebot-' + (object.name or '').replace('/','') + '.pdf')",
            "en_US": "(object.state in ('draft','sent')) and ('Quotation-' + (object.name or '').replace('/','') + '.pdf')",
        }
        result = resolve_attachment_value(attachment, "en_US")
        assert "Quotation" in result
        assert "object.state" in result

    def test_fallback_lang_not_used_when_company_lang_matches(self):
        """Fallback_lang is not used when company_lang is present in dict."""
        attachment = {"de_DE": "Angebot.pdf", "en_US": "Quotation.pdf"}
        assert resolve_attachment_value(attachment, "de_DE", fallback_lang="en_US") == "Angebot.pdf"

    def test_single_language_dict(self):
        """Single-language dict always returns that value."""
        attachment = {"de_DE": "Bericht.pdf"}
        assert resolve_attachment_value(attachment, "en_US") == "Bericht.pdf"
