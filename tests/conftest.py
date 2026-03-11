"""Shared test fixtures for odoo-fast-report-mapper test suite."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


@pytest.fixture
def fixtures_dir():
    """Path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def yaml_test_dir():
    """Path to the existing yaml_test directory."""
    return Path(__file__).parent / "yaml_test"


@pytest.fixture
def sample_report_yaml_data():
    """Complete report YAML data as a dictionary (modern locale codes)."""
    return {
        "name": {"de_DE": "Verkaufsauftrag", "en_US": "Sales_Order"},
        "report_name": "eq_fr_core_sale_order",
        "report_type": "fast_report",
        "print_report_name": "Verkaufsauftrag",
        "report_model": "sale.order",
        "eq_export_type": "pdf",
        "eq_ignore_images": True,
        "eq_handling_html_fields": "standard",
        "eq_multiprint": "standard",
        "multi": False,
        "attachment": "Verkaufsauftrag.pdf",
        "attachment_use": False,
        "eq_print_button": False,
        "dependencies": ["sale", "account"],
        "report_fields": {
            "sale.order": ["id", "name", "partner_id", "amount_total"],
            "sale.order.line": ["product_id", "product_uom_qty", "price_unit"],
        },
        "calculated_fields": {
            "payment_text": {
                "eq_get_payment_terms": ["partner_id.lang", "currency_id"],
            },
        },
    }


@pytest.fixture
def sample_report_yaml_data_legacy():
    """Complete report YAML data with legacy language keys for backward compatibility testing."""
    return {
        "name": {"ger": "Verkaufsauftrag", "eng": "Sales_Order"},
        "report_name": "eq_fr_core_sale_order",
        "report_type": "fast_report",
        "print_report_name": "Verkaufsauftrag",
        "report_model": "sale.order",
        "eq_export_type": "pdf",
        "eq_ignore_images": True,
        "eq_handling_html_fields": "standard",
        "eq_multiprint": "standard",
        "multi": False,
        "attachment": "Verkaufsauftrag.pdf",
        "attachment_use": False,
        "eq_print_button": False,
        "dependencies": ["sale", "account"],
        "report_fields": {
            "sale.order": ["id", "name", "partner_id", "amount_total"],
            "sale.order.line": ["product_id", "product_uom_qty", "price_unit"],
        },
        "calculated_fields": {
            "payment_text": {
                "eq_get_payment_terms": ["partner_id.lang", "currency_id"],
            },
        },
    }


@pytest.fixture
def sample_report_yaml_data_with_company():
    """Report YAML data with multi-company configuration."""
    return {
        "name": {"de_DE": "Rechnung_MC", "en_US": "Invoice_MC"},
        "report_name": "eq_fr_core_account_move",
        "report_type": "fast_report",
        "print_report_name": "Rechnung",
        "report_model": "account.move",
        "company_id": [1, 3],
        "eq_export_type": "pdf",
        "eq_ignore_images": True,
        "eq_handling_html_fields": "standard",
        "eq_multiprint": "standard",
        "multi": False,
        "attachment": "Rechnung.pdf",
        "attachment_use": False,
        "eq_print_button": False,
        "dependencies": ["account"],
        "report_fields": {
            "account.move": ["id", "name", "partner_id", "amount_total"],
        },
        "calculated_fields": {},
    }


@pytest.fixture
def sample_report_yaml_data_dict_prn():
    """Report YAML data with per-language dict print_report_name (new format)."""
    return {
        "name": {"de_DE": "Angebot", "en_US": "Quotation"},
        "report_name": "eq_fr_sale_order",
        "report_type": "fast_report",
        "print_report_name": {
            "de_DE": "('Angebot-' + (object.name or '').replace('/','')",
            "en_US": "('Quotation-' + (object.name or '').replace('/','')",
        },
        "report_model": "sale.order",
        "eq_export_type": "pdf",
        "eq_ignore_images": True,
        "eq_handling_html_fields": "standard",
        "eq_multiprint": "standard",
        "multi": False,
        "attachment": "Report.pdf",
        "attachment_use": False,
        "eq_print_button": False,
        "dependencies": ["sale"],
        "report_fields": {
            "sale.order": ["id", "name", "partner_id"],
        },
        "calculated_fields": {},
    }


@pytest.fixture
def sample_report_yaml_data_dict_attachment():
    """Report YAML data with per-language dict attachment (new format)."""
    return {
        "name": {"de_DE": "Angebot", "en_US": "Quotation"},
        "report_name": "eq_fr_sale_order",
        "report_type": "fast_report",
        "print_report_name": {
            "de_DE": "('Angebot-' + (object.name or '').replace('/','')",
            "en_US": "('Quotation-' + (object.name or '').replace('/','')",
        },
        "report_model": "sale.order",
        "eq_export_type": "pdf",
        "eq_ignore_images": True,
        "eq_handling_html_fields": "standard",
        "eq_multiprint": "standard",
        "multi": False,
        "attachment": {
            "de_DE": "(object.state in ('draft','sent')) and ('Angebot-' + (object.name or '').replace('/','') + '.pdf') or ('Auftrag-' + (object.name or '').replace('/','') + '.pdf')",
            "en_US": "(object.state in ('draft','sent')) and ('Quotation-' + (object.name or '').replace('/','') + '.pdf') or ('Order-' + (object.name or '').replace('/','') + '.pdf')",
        },
        "attachment_use": True,
        "eq_print_button": False,
        "dependencies": ["sale"],
        "report_fields": {
            "sale.order": ["id", "name", "partner_id"],
        },
        "calculated_fields": {},
    }


@pytest.fixture
def sample_connection_yaml_data():
    """Server connection YAML data as a dictionary."""
    return {
        "Server": {
            "url": "https://odoo.example.com",
            "port": 443,
            "user": "admin",
            "password": "test_password",
            "database": "test_db",
            "language": "ger",
            "collect_yaml": False,
            "disable_qweb": True,
            "workflow": 0,
        }
    }


@pytest.fixture
def mock_odoorpc():
    """Patch odoo_report_helper.utils.ODOO to prevent real network connections."""
    with patch("odoo_report_helper.utils.ODOO") as mock_odoo_cls:
        mock_instance = MagicMock()
        mock_instance.version = "18.0"
        mock_instance.env = MagicMock()
        mock_instance.env.context = {}
        mock_instance.config = {}
        mock_odoo_cls.return_value = mock_instance
        yield mock_odoo_cls


@pytest.fixture
def mock_odoo_env(mock_odoorpc):
    """Mock Odoo environment with common models."""
    mock_instance = mock_odoorpc.return_value

    # Mock ir.model
    mock_ir_model = MagicMock()
    mock_ir_model.search.return_value = [1]

    # Mock ir.model.fields
    mock_ir_model_fields = MagicMock()
    mock_ir_model_fields.search.return_value = [1]
    mock_ir_model_fields.eq_get_field_report_ids.return_value = []

    # Mock ir.actions.report
    mock_ir_actions_report = MagicMock()
    mock_ir_actions_report.search.return_value = [1]
    mock_ir_actions_report.create.return_value = 1
    mock_ir_actions_report.env = MagicMock()
    mock_ir_actions_report.env.user = MagicMock()
    mock_ir_actions_report.env.user.company_id = 1

    # Mock ir.module.module
    mock_ir_module = MagicMock()
    mock_ir_module.search.return_value = [1]

    # Mock res.lang for multi-language support
    mock_res_lang = MagicMock()
    mock_res_lang.search.return_value = [1, 2]
    mock_lang_de = MagicMock()
    mock_lang_de.code = "de_DE"
    mock_lang_de.iso_code = "de"
    mock_lang_de.name = "German / Deutsch"
    mock_lang_en = MagicMock()
    mock_lang_en.code = "en_US"
    mock_lang_en.iso_code = "en"
    mock_lang_en.name = "English (US)"
    mock_res_lang.browse.side_effect = lambda x: {
        "1": mock_lang_de,
        "2": mock_lang_en,
        1: mock_lang_de,
        2: mock_lang_en,
    }.get(x, MagicMock())

    def mock_env_getitem(key):
        env_map = {
            "ir.model": mock_ir_model,
            "ir.model.fields": mock_ir_model_fields,
            "ir.actions.report": mock_ir_actions_report,
            "ir.module.module": mock_ir_module,
            "res.lang": mock_res_lang,
        }
        return env_map.get(key, MagicMock())

    mock_instance.env.__getitem__ = mock_env_getitem

    return {
        "instance": mock_instance,
        "ir.model": mock_ir_model,
        "ir.model.fields": mock_ir_model_fields,
        "ir.actions.report": mock_ir_actions_report,
        "ir.module.module": mock_ir_module,
        "res.lang": mock_res_lang,
    }


@pytest.fixture
def tmp_yaml_dir(tmp_path):
    """Temporary directory with sample YAML files."""
    yaml_dir = tmp_path / "yaml_reports"
    yaml_dir.mkdir()

    report_data = {
        "name": {"de_DE": "Test_Report", "en_US": "Test_Report"},
        "report_name": "eq_fr_test",
        "report_type": "fast_report",
        "print_report_name": "Test",
        "report_model": "sale.order",
        "eq_export_type": "pdf",
        "eq_ignore_images": True,
        "eq_handling_html_fields": "standard",
        "eq_multiprint": "standard",
        "multi": False,
        "attachment": "Test.pdf",
        "attachment_use": False,
        "eq_print_button": False,
        "dependencies": ["sale"],
        "report_fields": {"sale.order": ["id", "name"]},
        "calculated_fields": {},
    }

    with open(yaml_dir / "test_report.yaml", "w") as f:
        yaml.dump(report_data, f)

    return yaml_dir


@pytest.fixture
def tmp_env_file(tmp_path):
    """Temporary .env file with test configuration."""
    env_content = """ODOO_URL=https://test.example.com
ODOO_PORT=443
ODOO_USER=admin
ODOO_PASSWORD=test_password
ODOO_DATABASE=test_db
ODOO_LANGUAGE=ger
ODOO_COLLECT_YAML=False
ODOO_DISABLE_QWEB=True
ODOO_WORKFLOW=0
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    return env_file
