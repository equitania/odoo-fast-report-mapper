# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Merged OdooConnection class — single, standalone implementation.

Combines the base OdooConnection (formerly in odoo_report_helper/odoo_connection.py)
and the extended EqOdooConnection (formerly in eq_odoo_connection.py) into one class
with no inheritance hierarchy. The circular import
(odoo_report_helper -> lang_utils -> odoo_fast_report_mapper) is eliminated.
"""

from __future__ import annotations

import os
import urllib.error
from datetime import datetime
from random import choice
from typing import Any, Literal, cast

import yaml
from odoorpc_toolbox import RPCError

from ._exceptions import OdooConnectionError
from ._lang_utils import build_name_search_domain, get_primary_lang, resolve_attachment_value
from ._logging import get_logger
from ._progress import progress_bar
from ._utils import prepare_connection
from ._yaml_dumper import YAMLDumper

logger = get_logger(__name__)


class OdooConnection:
    """
    Merged Odoo connection class — all connection, mapping, and collection logic
    in one place. No base-class inheritance.
    """

    def __init__(
        self,
        language: str,
        collect_yaml: bool,
        disable_qweb: bool,
        workflow: int,
        url: str,
        port: int,
        username: str,
        password: str,
        database: str,
        auth_method: str = "password",
    ) -> None:
        self.url = url
        self.port = port
        self.username = username
        self.password: str | None = password  # cleared to None after login for security
        self.database = database
        self.version = ""
        self.language = language
        self.collect_yaml = collect_yaml
        self.disable_qweb = disable_qweb
        self.workflow = workflow
        self.auth_method = auth_method  # 'password' or 'api_key'
        try:
            self.connection = prepare_connection(url, port)
        except urllib.error.URLError as ex:
            # Clear password from memory on connection failure
            self.password = None
            raise OdooConnectionError("ERROR: Please check your parameters and your connection" + " " + str(ex)) from ex

    def __repr__(self) -> str:
        return f"OdooConnection(username={self.username!r}, database={self.database!r})"

    def __str__(self) -> str:
        return self.__repr__()

    def login(self) -> None:
        """
        Try to login into the Odoo system and set parameters to optimize the connection.
        """
        try:
            if self.password is None:
                raise OdooConnectionError(
                    "Password must be set before login (already cleared after a previous login call)"
                )
            self.connection.login(self.database, self.username, self.password)
            # Change settings to make the connection faster
            self.connection.config["auto_commit"] = True  # No need for manual commits
            self.connection.env.context["active_test"] = False  # Show inactive articles
            self.connection.env.context["tracking_disable"] = True
            self.version = self.connection.version.split(".")[0]
            # Clear password from memory after successful login
            self.password = None
            logger.info(f"Connected to database: {self.database}")
        except RPCError as ex:
            raise OdooConnectionError("ERROR: Please check your parameters and your connection" + " " + str(ex)) from ex

    def _get_fast_report_ids(self) -> list[int]:
        """
        Returns all report IDs that have report_type = fast_report.

        :return: List of report_ids
        """
        IR_ACTIONS_REPORT = self.connection.env["ir.actions.report"]
        report_ids = IR_ACTIONS_REPORT.search([("report_type", "=", "fast_report")])
        return cast(list[int], report_ids)  # Any: Odoo RPC returns list of int IDs

    def check_module(self, module_name: str) -> bool:
        """
        Search for module in Odoo and return True when it is installed, else return false.

        :param: module_name: Name of module
        """
        IR_MODULE_MODULE = self.connection.env["ir.module.module"]
        module_id = IR_MODULE_MODULE.search([("state", "=", "installed"), ("name", "=", module_name)])
        return bool(module_id)

    def check_api_key_compatibility(self) -> None:
        """Verify the Odoo server supports API-key authentication (>= v14).

        Queries server version BEFORE login (uses unauthenticated common.version
        endpoint). Only enforced when auth_method == 'api_key'.

        Raises:
            ValueError: If auth_method is 'api_key' and the server major version < 14.
        """
        if self.auth_method != "api_key":
            return
        try:
            server_version = self.connection.version
            major = int(server_version.split(".")[0])
        except (AttributeError, ValueError, IndexError) as ex:
            raise ValueError(f"Could not determine Odoo server version for API-key compatibility check: {ex}") from ex
        if major < 14:
            raise ValueError(
                f"API-key authentication requires Odoo >= 14, but server reports v{server_version}. "
                "Use ODOO_PASSWORD instead, or upgrade the Odoo server."
            )

    def get_installed_languages(self) -> list[dict[str, Any]]:
        """Query res.lang for all active languages in Odoo.

        Returns:
            list of dicts with 'code' (e.g. 'de_DE'), 'iso_code' (e.g. 'de'), 'name'.
        """
        RES_LANG = self.connection.env["res.lang"]
        lang_ids = RES_LANG.search([("active", "=", True)])
        languages = []
        for lang_id in lang_ids:
            lang_obj = RES_LANG.browse(lang_id)
            languages.append(
                {
                    "code": lang_obj.code,
                    "iso_code": lang_obj.iso_code,
                    "name": lang_obj.name,
                }
            )
        logger.info(f"Installed languages: {[lang['code'] for lang in languages]}")
        return languages

    def get_company_language(self, company_id: int) -> str:
        """Look up company language from res.company.partner_id.lang.

        Cached per company_id. Falls back to self.language when the partner
        language is empty or an RPC error occurs.

        Args:
            company_id: Odoo res.company ID (integer).

        Returns:
            Odoo locale code string (e.g. 'de_DE').
        """
        if not hasattr(self, "_company_lang_cache"):
            self._company_lang_cache: dict[int, str] = {}
        if company_id in self._company_lang_cache:
            return self._company_lang_cache[company_id]
        try:
            company_obj = self.connection.env["res.company"].browse(company_id)
            lang = company_obj.partner_id.lang or self.language
        except (RPCError, KeyError, AttributeError) as ex:
            logger.debug(
                f"Could not determine language for company {company_id}, falling back to {self.language}: {ex}"
            )
            lang = self.language
        self._company_lang_cache[company_id] = lang
        return lang

    def _search_report_v13(
        self,
        model_name: str,
        report_name: dict[str, str],
        IR_ACTIONS_REPORT: Any | None = None,  # Any: odoorpc proxy object, no typed class
        company_id: int | None = None,
    ) -> int | Literal[False]:
        if not IR_ACTIONS_REPORT:
            IR_ACTIONS_REPORT = self.connection.env["ir.actions.report"]
        name_domain = build_name_search_domain(report_name)
        company_domain = ["|", ("company_id", "=", company_id), ("company_id", "=", False)] if company_id else []
        report_ids = IR_ACTIONS_REPORT.search([("model", "=ilike", model_name)] + name_domain + company_domain)
        if len(report_ids) == 0:
            return False
        return cast(int, report_ids[0])  # Any: Odoo RPC returns int ID

    def _search_report(
        self,
        model_name: str,
        report_name: dict[str, str],
        IR_ACTIONS_REPORT: Any | None = None,  # Any: odoorpc proxy object, no typed class
        company_id: int | None = None,
    ) -> int | Literal[False]:
        if not IR_ACTIONS_REPORT:
            IR_ACTIONS_REPORT = self.connection.env["ir.actions.report"]
        name_domain = build_name_search_domain(report_name)
        domain = [("model", "=ilike", model_name)] + name_domain
        if company_id:
            domain += ["|", ("company_id", "=", company_id), ("company_id", "=", False)]
        report_ids = IR_ACTIONS_REPORT.search(domain)
        if len(report_ids) == 0:
            return False
        return cast(int, report_ids[0])  # Any: Odoo RPC returns int ID

    def check_dependencies(self, dependencies: list[str] | Literal[False]) -> tuple[bool, list[str]]:
        """
        Check if all dependencies (modules) are installed, if one isn't, return False.

        :param: dependencies: List of names of modules
        """
        not_installed_modules = []
        if dependencies:
            for dependency in dependencies:
                dependency_installed = self.check_module(dependency)
                if not dependency_installed:
                    not_installed_modules.append(dependency)
            if not_installed_modules:
                return False, not_installed_modules
        return True, not_installed_modules

    def map_reports(self, report_list: list[Any]) -> list[tuple[str, str]]:
        """
        Create/Write reports into the Odoo system with their fields and properties.

        Returns a list of (report_name, error_message) tuples for failed reports.
        """
        IR_MODEL = self.connection.env["ir.model"]
        IR_MODEL_FIELDS = self.connection.env["ir.model.fields"]
        IR_ACTIONS_REPORT = self.connection.env["ir.actions.report"]
        models_fields: dict[int, dict[int, list[int]]] = {}
        model_name_ids: dict[str, int] = {}
        failed_reports = []

        # Fetch installed languages once for multi-language translation
        installed_langs = self.get_installed_languages()
        installed_lang_codes = {lang["code"] for lang in installed_langs}

        logger.info(f"→ Mapping {len(report_list)} reports to Odoo...")
        for idx, report in enumerate(report_list, 1):
            logger.info(f"  [{idx}/{len(report_list)}] {report.report_name}")
            try:
                report_object, ok = self._create_or_update_report(report, IR_ACTIONS_REPORT, installed_lang_codes)
                if not ok:
                    failed_reports.append((report.report_name, "Dependencies not installed"))
                    continue

                self._set_report_translations(report, report_object, installed_lang_codes)
                self._map_report_fields(report, report_object, IR_MODEL, IR_MODEL_FIELDS, models_fields, model_name_ids)
                logger.info(f"  ✓ Completed: {report.report_name}")
            except (RPCError, KeyError, AttributeError, ValueError, IndexError) as ex:
                logger.error(f"  ✗ Failed: {report.report_name} — {ex}")
                failed_reports.append((report.report_name, str(ex)))
                continue

        self._write_field_mappings(models_fields, IR_MODEL)
        return failed_reports

    def _create_or_update_report(
        self,
        report: Any,  # Any: Report object — forward import to avoid circular ref
        IR_ACTIONS_REPORT: Any,  # Any: odoorpc proxy object, no typed class
        installed_lang_codes: set[str],
    ) -> tuple[Any, bool]:
        """Search for existing report and create or update it in Odoo.

        Handles dependency check, company switching, report search, create/update,
        and create_action. Resolves attachment dict to single value and sets primary
        language name in _data_dictionary.

        Args:
            report: Report object to process.
            IR_ACTIONS_REPORT: Odoo ir.actions.report model proxy.
            installed_lang_codes: Set of installed language codes.

        Returns:
            Tuple of (report_object, success). report_object is the browsed record
            (or None on failure), success is bool.
        """
        original_company_yaml_user = IR_ACTIONS_REPORT.env.user.company_id

        report.self_ensure()
        # Use primary language from name dict for default report name
        primary_lang = get_primary_lang(report.entry_name)
        report._data_dictionary["name"] = report.entry_name[primary_lang]
        # Resolve attachment dict to single value based on company language
        if isinstance(report.attachment, dict):
            company_id_val = report.company_id[0] if report.company_id else False
            if company_id_val:
                company_lang = self.get_company_language(company_id_val)
            else:
                company_lang = self.language
            report._data_dictionary["attachment"] = resolve_attachment_value(
                report.attachment, company_lang, fallback_lang=self.language
            )
            logger.debug(f"    Resolved attachment for company lang [{company_lang}]")
        dependencies_installed, not_installed_modules = self.check_dependencies(report._dependencies)
        if not dependencies_installed and not_installed_modules:
            logger.error(f"  ✗ Dependencies for {report.report_name} not installed")
            for not_installed_module in not_installed_modules:
                logger.error(f"    - Module '{not_installed_module}' missing")
            return None, False
        if report.company_id:
            IR_ACTIONS_REPORT.env.user.company_id = report.company_id[0]
            if self.version in ["13", "14", "15", "16"]:
                report_id = self._search_report_v13(
                    report.model_name,
                    report.entry_name,
                    IR_ACTIONS_REPORT,
                    report.company_id[0],
                )
            else:
                report_id = self._search_report(
                    report.model_name, report.entry_name, IR_ACTIONS_REPORT, company_id=report.company_id[0]
                )
        else:
            report_id = self._search_report(report.model_name, report.entry_name, IR_ACTIONS_REPORT)
        if not report_id:
            report_id = IR_ACTIONS_REPORT.create(report._data_dictionary)
            report_object = IR_ACTIONS_REPORT.browse(report_id)
        else:
            report_object = IR_ACTIONS_REPORT.browse(report_id)
            report_object.write(report._data_dictionary)
        # Add report to print menu
        report_object.create_action()

        IR_ACTIONS_REPORT.env.user.company_id = original_company_yaml_user

        return report_object, True

    def _set_report_translations(
        self,
        report: Any,  # Any: Report object — forward import to avoid circular ref
        report_object: Any,  # Any: odoorpc proxy object, no typed class
        installed_lang_codes: set[str],
    ) -> None:
        """Write name and print_report_name translations per installed language.

        Args:
            report: Report object with entry_name and print_report_name.
            report_object: Browsed ir.actions.report record.
            installed_lang_codes: Set of installed language codes.
        """
        # Set translations for all installed languages
        for lang_code, translated_name in report.entry_name.items():
            if lang_code in installed_lang_codes:
                report_object.with_context(lang=lang_code).write({"name": translated_name})
                logger.debug(f"    Set name [{lang_code}]: {translated_name}")

        # Set print_report_name translations
        if report.print_report_name:
            if isinstance(report.print_report_name, dict):
                # Per-language dict: write each language's expression
                for lang_code, prn_value in report.print_report_name.items():
                    if lang_code in installed_lang_codes:
                        report_object.with_context(lang=lang_code).write({"print_report_name": prn_value})
                        logger.debug(f"    Set print_report_name [{lang_code}]")
            else:
                # Legacy single string: write to all installed languages
                for lang_code in installed_lang_codes:
                    report_object.with_context(lang=lang_code).write({"print_report_name": report.print_report_name})
            logger.debug("    print_report_name configured")

    def _map_report_fields(
        self,
        report: Any,  # Any: Report object — forward import to avoid circular ref
        report_object: Any,  # Any: odoorpc proxy object, no typed class
        IR_MODEL: Any,  # Any: odoorpc proxy object, no typed class
        IR_MODEL_FIELDS: Any,  # Any: odoorpc proxy object, no typed class
        models_fields: dict[int, dict[int, list[int]]],
        model_name_ids: dict[str, int],
    ) -> None:
        """Iterate report fields, search model/field IDs, and build models_fields dict.

        Also sets calculated fields for the report.

        Args:
            report: Report object with _fields and _calculated_fields.
            report_object: Browsed ir.actions.report record.
            IR_MODEL: Odoo ir.model model proxy.
            IR_MODEL_FIELDS: Odoo ir.model.fields model proxy.
            models_fields: Dict accumulator {model_id: {field_id: [report_ids]}}, modified in-place.
            model_name_ids: Dict cache {model_name: model_id}, modified in-place.
        """
        # Count total fields for logging
        total_fields = sum(len(fields) for fields in report._fields.values())
        logger.debug(f"    Mapping {total_fields} fields across {len(report._fields)} models...")

        # Loop over all models in report fields dictionary
        for model_name in report._fields:
            # Get model object in Odoo
            if model_name in model_name_ids:
                model_id = model_name_ids[model_name]
            else:
                model_id = IR_MODEL.search([("model", "=", model_name)])
                if model_id:
                    model_name_ids[model_name] = model_id[0]
                    model_id = model_id[0]
            # Loop over all fields in the list of the current model
            if model_id:
                for field_name in report._fields[model_name]:
                    # Get the field from Odoo
                    field_id = IR_MODEL_FIELDS.search([("model_id", "=", model_id), ("name", "=", field_name)])
                    if field_id:
                        report_list_ids = IR_MODEL_FIELDS.eq_get_field_report_ids(field_id)
                        if report_object.id not in report_list_ids:
                            # Create dict of dicts in order to store the ids with the following structure:
                            # {model_id: {field_id1: [report_ids], field_id2: [report_ids]}
                            report_ids = report_list_ids + [report_object.id]
                            if model_id in models_fields:
                                if field_id[0] in models_fields[model_id]:
                                    new_report_ids = models_fields[model_id][field_id[0]] + report_ids
                                    models_fields[model_id][field_id[0]] = list(dict.fromkeys(new_report_ids))
                                else:
                                    models_fields[model_id][field_id[0]] = report_ids
                            else:
                                models_fields[model_id] = dict()
                                models_fields[model_id][field_id[0]] = report_ids
                    else:
                        logger.warning(f"Field '{field_name}' not found in model '{model_name}'")
            else:
                logger.warning(f"Model '{model_name}' not found in system")
        if report._calculated_fields:
            report_company_id = report.company_id[0] if report.company_id else False
            for field, content in report._calculated_fields.items():
                for function_name, parameter in content.items():
                    self.set_calculated_fields(
                        field,
                        function_name,
                        parameter,
                        report.entry_name,
                        report.model_name,
                        report_company_id,
                    )

    def _write_field_mappings(
        self,
        models_fields: dict[int, dict[int, list[int]]],
        IR_MODEL: Any,  # Any: odoorpc proxy object, no typed class
    ) -> None:
        """Write accumulated field mappings to Odoo models.

        Args:
            models_fields: Dict {model_id: {field_id: [report_ids]}} built by _map_report_fields.
            IR_MODEL: Odoo ir.model model proxy.
        """
        # Final step: Write field mappings to Odoo models
        logger.info(f"→ Writing field mappings to {len(models_fields)} models...")
        for idx, model in enumerate(models_fields, 1):
            try:
                fields_list = []
                for field in models_fields[model]:
                    fields_list.append(
                        (
                            1,
                            field,
                            {"eq_report_ids": [(6, 0, models_fields[model][field])]},
                        )
                    )

                # Get model name for logging
                model_obj = IR_MODEL.browse(model)
                model_name = model_obj.model if model_obj else f"model_id_{model}"
                logger.info(f"  [{idx}/{len(models_fields)}] Updating {model_name} ({len(fields_list)} fields)...")

                # Write/update the report_ids using odoo helper function: eq_write_report_ids defined in eq_fr_core module
                IR_MODEL.eq_write_report_ids(model, fields_list)
            except (RPCError, KeyError, AttributeError) as ex:
                logger.error(f"  ✗ Exception while writing report IDs to model {model}")
                logger.exception(ex)

        logger.info("✓ Field mapping completed successfully")

    def set_calculated_fields(
        self,
        field_name: str,
        function_name: str,
        parameters: list[str],
        report_name: dict[str, str],
        report_model: str,
        report_company_id: int | Literal[False],
    ) -> None:
        """
        Set calculated fields for the report and clean them.

        Example:
        {
            'field_name': {'function_name': ['parameter1', 'parameter2']},
            'payment_text': {'eq_get_payment_terms': ['partner_id.lang', 'currency_id']}
        }
        """
        IR_ACTIONS_REPORT: Any = self.connection.env["ir.actions.report"]  # Any: odoorpc proxy
        REPORT_CALC: Any = self.connection.env["eq_calculated_field_value"]  # Any: odoorpc proxy
        parameters_as_string = ", ".join(parameters)
        parameters_as_string = parameters_as_string.strip()
        value_dict = {
            "eq_field_name": field_name,
            "eq_function_name": function_name,
            "eq_parameters_name": parameters_as_string,
        }
        name_domain = build_name_search_domain(report_name)
        base_domain = [("model", "=", report_model), ("report_type", "=", "fast_report")]
        if report_company_id:
            IR_ACTIONS_REPORT.env.user.company_id = report_company_id
            company_domain = ["|", ("company_id", "=", report_company_id), ("company_id", "=", False)]
            report_id = IR_ACTIONS_REPORT.search(base_domain + name_domain + company_domain)
        else:
            report_id = IR_ACTIONS_REPORT.search(base_domain + name_domain)
        if not report_id:
            logger.error(f"Cannot set calculated fields: report not found for model={report_model}")
            return
        value_dict["eq_report_id"] = report_id[0]
        calculated_field_id = REPORT_CALC.search(
            [("eq_report_id", "=", report_id[0]), ("eq_field_name", "=", field_name)]
        )
        if len(calculated_field_id) == 0:
            REPORT_CALC.create(value_dict)
        else:
            REPORT_CALC.write(calculated_field_id, value_dict)

    def list_fast_reports(self) -> list[dict[str, Any]]:
        """List all FastReport entries across all user companies.

        Returns:
            list of dicts: [{id, report_name, name, model, company, export_type}, ...]
            Deduplicated by report_name (same logic as collect_all_report_entries).
        """
        company_ids = (
            self.connection.env.user.company_ids.ids
            if self.connection.env.user.company_ids
            else self.connection.env.user.company_id.ids
        )
        seen_report_names = {}
        results = []

        for company_id in company_ids:
            self.connection.env.user.company_id = company_id

            if self.version == "10":
                IR_ACTIONS_REPORT = self.connection.env["ir.actions.report.xml"]
            else:
                IR_ACTIONS_REPORT = self.connection.env["ir.actions.report"]

            company_name = self.connection.env["res.company"].browse(company_id).name

            report_ids = IR_ACTIONS_REPORT.search([("report_type", "=", "fast_report")])

            for report_id in report_ids:
                report_obj = IR_ACTIONS_REPORT.browse(report_id)
                rname = report_obj.report_name

                if rname in seen_report_names:
                    continue
                seen_report_names[rname] = report_id

                results.append(
                    {
                        "id": report_id,
                        "report_name": rname,
                        "name": report_obj.name,
                        "model": report_obj.model,
                        "company": company_name,
                        "export_type": report_obj.eq_export_type,
                    }
                )

        return results

    def collect_all_report_entries(self, output_path: str) -> None:
        """Backward-compatible wrapper for collect_report_entries."""
        self.collect_report_entries(output_path)

    def collect_report_entries(self, output_path: str, report_ids: list[int] | None = None) -> None:
        """Collect FastReport entries from Odoo and write them as YAML files.

        Args:
            output_path: Directory path to write YAML files to.
            report_ids: Optional list of report IDs to filter. If None, collects all.
        """
        company_ids = (
            self.connection.env.user.company_ids.ids
            if self.connection.env.user.company_ids
            else self.connection.env.user.company_id.ids
        )
        report_name_id_combination: dict[str, int] = {}
        data_dictionary: dict[
            Any, Any
        ] = {}  # Any: keys are int report IDs, values are nested Odoo report field data (Tier 2)
        for company_id in company_ids:
            # Change the current company in the env
            self.connection.env.user.company_id = company_id

            if self.version == "10":
                IR_ACTIONS_REPORT = self.connection.env["ir.actions.report.xml"]
            else:
                IR_ACTIONS_REPORT = self.connection.env["ir.actions.report"]
            data_dictionary_keys = list(data_dictionary.keys())
            search_domain: list[Any] = [  # Any: Odoo domain tuples have mixed value types
                ("report_type", "=", "fast_report"),
                ("id", "not in", data_dictionary_keys),
            ]
            if report_ids is not None:
                search_domain.append(("id", "in", report_ids))
            found_ids = IR_ACTIONS_REPORT.search(search_domain)

            IR_MODEL_FIELDS = self.connection.env["ir.model.fields"]
            all_report_field_ids = IR_MODEL_FIELDS.search(
                [("eq_report_ids", "in", found_ids), ("eq_report_ids", "!=", False)]
            )

            # Get current company name
            company_name = self.connection.env["res.company"].browse(company_id).name
            logger.info(f"Collecting fields for company: {company_name}")

            for field_id in progress_bar(
                all_report_field_ids, desc=f"Collecting fields ({company_name})", unit="field"
            ):
                # Get object
                field_object = IR_MODEL_FIELDS.browse(field_id)
                # Get attributes
                report_action_ids = field_object.eq_report_ids.ids
                model_id = field_object.model_id
                model_name = model_id.model
                field_name = field_object.name
                raw_modules = field_object.modules or ""
                modules = [m for m in raw_modules.replace(" ", "").split(",") if m]

                # Add field to dictionary
                for report_action_id in report_action_ids:
                    report_action_object = IR_ACTIONS_REPORT.browse(report_action_id)
                    report_company_id = report_action_object.company_id.id if report_action_object.company_id else False
                    if report_company_id:
                        if (
                            report_action_object.report_name in report_name_id_combination
                            and report_action_id != report_name_id_combination[report_action_object.report_name]
                        ):
                            if (
                                "company_id"
                                in data_dictionary[report_name_id_combination[report_action_object.report_name]]
                                and report_company_id
                                not in data_dictionary[report_name_id_combination[report_action_object.report_name]][
                                    "company_id"
                                ]
                            ):
                                data_dictionary[report_name_id_combination[report_action_object.report_name]][
                                    "company_id"
                                ].append(report_company_id)
                            continue
                        else:
                            report_name_id_combination[report_action_object.report_name] = report_action_id
                    data_dictionary = self.add_field_to_dictionary(
                        data_dictionary,
                        report_action_id,
                        model_name,
                        field_name,
                        report_company_id,
                        modules,
                    )
        for report_action_id, fields in data_dictionary.items():
            # Create report object
            eq_report_object = self.create_eq_report_object(report_action_id, fields)
            eq_yaml_data = eq_report_object.ensure_data_for_yaml()

            # Get timestamp
            now = datetime.now()
            date_now = now.strftime("%m_%d_%Y_%H_%M_%S")
            # Sanitize report_name to prevent path traversal (data comes from Odoo server)
            safe_name = os.path.basename(eq_report_object.report_name).replace("..", "")
            if not safe_name:
                logger.warning(f"Skipping report with invalid name: {eq_report_object.report_name!r}")
                continue
            output_name = os.path.join(output_path, safe_name + "_" + date_now + ".yaml")
            # Verify resolved path stays within output directory
            if not os.path.realpath(output_name).startswith(os.path.realpath(output_path) + os.sep):
                logger.error(f"Path traversal detected, skipping: {eq_report_object.report_name!r}")
                continue
            self.write_yaml(output_name, eq_yaml_data)

    def add_field_to_dictionary(
        self,
        data_dictionary: dict[Any, Any],
        report_id: Any,  # Any: Odoo record ID (int or odoorpc proxy)
        model_name: str,
        field_name: str,
        company_id: int | Literal[False],
        modules: list[str] | None = None,  # resolved by caller from field_object.modules; None means no dependency info
    ) -> dict[Any, Any]:
        """Add a single model field to the per-report mapping dictionary.

        Creates the report/model entries on first use and appends the field and
        any company id without introducing duplicates.

        :param data_dictionary: accumulator keyed by report id, then model name
        :param report_id: Odoo report record id
        :param model_name: technical model name the field belongs to
        :param field_name: technical field name to map
        :param company_id: company id to scope the report to, or ``False``
        :param modules: modules providing the field (for dependency info), or None
        :return: the updated ``data_dictionary``
        """
        if report_id not in data_dictionary:
            data_dictionary[report_id] = {}
        if model_name not in data_dictionary[report_id]:
            data_dictionary[report_id][model_name] = [field_name]
        if field_name not in data_dictionary[report_id][model_name]:
            data_dictionary[report_id][model_name].append(field_name)
        if company_id:
            if "company_id" not in data_dictionary[report_id]:
                data_dictionary[report_id]["company_id"] = [company_id]
            elif company_id not in data_dictionary[report_id]["company_id"]:
                data_dictionary[report_id]["company_id"].append(company_id)
        modules_dependencies = modules or []
        if not modules_dependencies:
            return data_dictionary
        if "dependencies" in data_dictionary[report_id]:
            data_dictionary[report_id]["dependencies"].extend(modules_dependencies)
            data_dictionary[report_id]["dependencies"] = list(set(data_dictionary[report_id]["dependencies"]))
        else:
            data_dictionary[report_id]["dependencies"] = list(modules_dependencies)
        return data_dictionary

    def _collect_calculated_fields(self, eq_calculated_field_objects: Any) -> dict[str, Any]:  # Any: odoorpc recordset
        """
        Get calculated fields from eq_calculated_field model objects.

        Example:
        {
            'field_name': {'function_name': ['parameter1', 'parameter2']},
        }
        """
        eq_calculated_field_dict = {}

        for eq_calculated_field in eq_calculated_field_objects:
            eq_calculated_field_field_name = eq_calculated_field.eq_field_name
            eq_calculated_field_func_name = eq_calculated_field.eq_function_name
            eq_calculated_field_params_name = eq_calculated_field.eq_parameters_name
            eq_calculated_field_dict[eq_calculated_field_field_name] = {
                eq_calculated_field_func_name: eq_calculated_field_params_name.replace(" ", "").split(",")
            }
        return eq_calculated_field_dict

    def create_eq_report_object(
        self, action_id: Any, field_dictionary: dict[str, Any]
    ) -> Any:  # Any: Report object (circular import avoided)
        """Build a :class:`Report` object from an existing Odoo report action.

        Reads the report action via RPC, collects its name in all installed
        languages and assembles a :class:`Report` populated with the given field
        dictionary — used by the collect workflow to export Odoo reports to YAML.

        :param action_id: id of the ``ir.actions.report`` record
        :param field_dictionary: collected field mapping for this report
        :return: a populated :class:`Report` instance
        """
        # Lazy import to avoid forward-reference before _report.py exists in Wave 3
        from ._report import Report  # noqa: PLC0415

        if self.version == "10":
            IR_ACTIONS_REPORT = self.connection.env["ir.actions.report.xml"]
        else:
            IR_ACTIONS_REPORT = self.connection.env["ir.actions.report"]
        if "company_id" in field_dictionary:
            self.connection.env.user.company_id = field_dictionary["company_id"][0]
        action_object = IR_ACTIONS_REPORT.browse(action_id)
        # Collect name in all installed languages
        installed_langs = self.get_installed_languages()
        name = {}
        for lang in installed_langs:
            lang_code = lang["code"]
            translated_name = action_object.with_context(lang=lang_code).name
            if translated_name:
                name[lang_code] = translated_name
        # Fallback: ensure at least primary language is present
        if not name:
            name = {self.language: action_object.name}
        report_name = action_object.report_name
        report_type = action_object.report_type
        eq_export_type = action_object.eq_export_type
        # Collect print_report_name in all installed languages (same pattern as name)
        _prn_dict: dict[str, Any] = {}
        for lang in installed_langs:
            lang_code = lang["code"]
            translated_prn = action_object.with_context(lang=lang_code).print_report_name
            if translated_prn:
                _prn_dict[lang_code] = translated_prn
        print_report_name: dict[str, Any] | str = _prn_dict if _prn_dict else action_object.print_report_name or ""
        model_name = action_object.model
        eq_ignore_images = action_object.eq_ignore_images
        eq_handling_html_fields = action_object.eq_handling_html_fields
        multi = action_object.multi
        attachment_use = action_object.attachment_use
        attachment = action_object.attachment
        eq_calculated_field_ids = action_object.eq_calculated_field_ids
        company_id = field_dictionary.pop("company_id", False)
        dependencies = sorted(field_dictionary.pop("dependencies", []))

        calculated_fields_dict = self._collect_calculated_fields(eq_calculated_field_ids)
        if not self.is_dict(calculated_fields_dict):
            calculated_fields_dict = {}
        eq_print_button = action_object.eq_print_button
        if not self.is_boolean(eq_print_button):
            eq_print_button = False
        eq_multiprint = action_object.eq_multiprint

        eq_report_obj = Report(
            name,
            report_name,
            report_type,
            model_name,
            company_id,
            eq_export_type,
            print_report_name,
            attachment,
            eq_ignore_images,
            eq_handling_html_fields,
            multi,
            attachment_use,
            eq_print_button,
            dependencies,
            field_dictionary,
            calculated_fields_dict,
            eq_multiprint,
        )
        return eq_report_obj

    def write_yaml(self, file_name: str, data: dict[str, Any]) -> None:
        """
        Write data to YAML file with UTF-8 encoding and custom formatting.

        :param file_name: Output file path
        :param data: Dictionary to be written as YAML
        """
        with open(file_name, "w", encoding="utf8") as outfile:
            yaml.dump(
                data,
                outfile,
                Dumper=YAMLDumper,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    def is_boolean(self, object_to_be_checked: Any) -> bool:
        """Return ``True`` if the given value is a ``bool``."""
        return bool(isinstance(object_to_be_checked, bool))

    def is_dict(self, object_to_be_checked: Any) -> bool:
        """Return ``True`` if the given value is a ``dict``."""
        return bool(isinstance(object_to_be_checked, dict))

    def test_fast_report_rendering(self, report_list: list[Any]) -> None:
        """
        Test FastReport rendering in the Odoo system.

        :param: report_list: List of report objects
        IMPORTANT: The FastReport API URL, connection and base report setup must be done before testing.
        """

        # Logging is now centrally configured via _logging.py
        original_company_yaml_user = self.connection.env.user.company_id
        try:
            for report in report_list:
                if report.company_id:
                    self.connection.env.user.company_id = report.company_id[0]
                    IR_ACTIONS_REPORT = self.connection.env["ir.actions.report"]
                    if self.version in ["13", "14", "15", "16"]:
                        report_id = self._search_report_v13(
                            report.model_name,
                            report.entry_name,
                            IR_ACTIONS_REPORT,
                            report.company_id[0],
                        )
                    else:
                        report_id = self._search_report(
                            report.model_name,
                            report.entry_name,
                            IR_ACTIONS_REPORT,
                            company_id=report.company_id[0],
                        )
                else:
                    IR_ACTIONS_REPORT = self.connection.env["ir.actions.report"]
                    report_id = self._search_report(report.model_name, report.entry_name, IR_ACTIONS_REPORT)
                # Get report action record
                if not report_id:
                    logger.warning(f"Report {report.report_name} not created or is not type FastReport")
                    continue
                report_object: Any = IR_ACTIONS_REPORT.browse(report_id)  # Any: odoorpc proxy — browse returns Model
                # Check if the report has been created and is type Fast Report
                if report_object.report_type != "fast_report":
                    logger.warning(f"Report {report.report_name} not created or is not type FastReport")
                    continue

                logger.info(f"Testing report rendering: {report.report_name}")

                # Get module from report model
                IR_REPORT_MODEL = self.connection.env[report.model_name]

                # Get all report model records ids
                report_model_records_ids = IR_REPORT_MODEL.search([])
                try:
                    if not len(report_model_records_ids):
                        logger.warning(f"No records for model {report.model_name}")
                        logger.info(f"Using demo data to test report: {report.report_name}")
                        # Render Fast Report for demo example databases
                        res, content_format = IR_ACTIONS_REPORT.eq_render_fast_report_empty_db(report_object.ids)
                    else:
                        # Render Fast Report for a random report model record, without creating attachment
                        res, content_format = IR_ACTIONS_REPORT.eq_render_fast_report(
                            report_object.ids,
                            [choice(report_model_records_ids)],
                            create_attachment=False,
                        )
                    logger.info(f"Report rendering successful: {report.report_name}")
                except FileNotFoundError:
                    logger.warning(f"No demo data to test report: {report.report_name}")
                except RPCError as ex:
                    logger.error(f"Report {report.report_name} not rendering correctly")
                    logger.error("Exception occurred during rendering")
                    logger.exception(ex)
        finally:
            self.connection.env.user.company_id = original_company_yaml_user

    def disable_qweb_reports(self) -> None:
        """Remove the print-menu actions of all QWeb (pdf/html/text) reports.

        Searches every ``ir.actions.report`` of type ``qweb-pdf``, ``qweb-html``
        or ``qweb-text`` and calls ``unlink_action()`` so only FastReport entries
        remain available in the print menu.
        """
        IR_ACTIONS_REPORT = self.connection.env["ir.actions.report"]
        report_ids = IR_ACTIONS_REPORT.search(
            [
                "|",
                ("report_type", "=", "qweb-pdf"),
                "|",
                ("report_type", "=", "qweb-html"),
                ("report_type", "=", "qweb-text"),
            ]
        )
        for report_id in report_ids:
            report_object = IR_ACTIONS_REPORT.browse(report_id)
            report_object.unlink_action()
        logger.info(f"Disabled QWeb reports for database: {self.database}")
