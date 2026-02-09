# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Tests for odoo_fast_report_mapper/progress.py - Progress bar utilities."""

import io
from unittest.mock import patch

from odoo_fast_report_mapper.progress import (
    ProgressBar,
    ReportProgress,
    create_progress_bar,
    progress_bar,
)

# Use a devnull stream to suppress tqdm output during tests.
# When disable=True, tqdm skips setting attributes like desc, colour, unit
# and update() does not increment n. So we use disable=False with a dummy file.
_devnull = io.StringIO()


# ---------------------------------------------------------------------------
# ProgressBar tests
# ---------------------------------------------------------------------------


class TestProgressBar:
    """Verify ProgressBar wrapper around tqdm."""

    def test_create_with_defaults(self):
        """ProgressBar must be creatable with default parameters."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ProgressBar(total=10)
        assert pbar.pbar is not None
        pbar.close()

    def test_create_with_custom_parameters(self):
        """ProgressBar must accept custom desc, unit, and colour."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ProgressBar(total=5, desc="Custom", unit="file", colour="blue")
        assert pbar.pbar is not None
        assert pbar.pbar.desc == "Custom"
        assert pbar.pbar.unit == "file"
        pbar.close()

    def test_default_colour_is_green(self):
        """ProgressBar must default to green colour."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ProgressBar(total=10)
        assert pbar.pbar.colour == "green"
        pbar.close()

    def test_update_increments(self):
        """ProgressBar.update must increment the progress counter."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ProgressBar(total=10)
        pbar.update(1)
        assert pbar.pbar.n == 1
        pbar.update(3)
        assert pbar.pbar.n == 4
        pbar.close()

    def test_update_default_increment(self):
        """ProgressBar.update must default to incrementing by 1."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ProgressBar(total=10)
        pbar.update()
        assert pbar.pbar.n == 1
        pbar.close()

    def test_set_description(self):
        """ProgressBar.set_description must update the description text."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ProgressBar(total=10, desc="Initial")
        pbar.set_description("Updated")
        # tqdm appends ': ' when using set_description
        assert "Updated" in pbar.pbar.desc
        pbar.close()

    def test_context_manager_enter(self):
        """ProgressBar must return self on context manager entry."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull), ProgressBar(total=5) as pbar:
            assert isinstance(pbar, ProgressBar)

    def test_context_manager_exit_closes(self):
        """ProgressBar context manager must close properly."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull), ProgressBar(total=5) as pbar:
            pbar.update(2)
        # After context manager exit, close has been called
        assert pbar.pbar is not None

    def test_context_manager_works_with_updates(self):
        """ProgressBar context manager must support updates inside block."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull), ProgressBar(total=3) as pbar:
            pbar.update(1)
            pbar.update(1)
            pbar.update(1)
            assert pbar.pbar.n == 3

    def test_set_postfix(self):
        """ProgressBar.set_postfix must accept keyword arguments."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ProgressBar(total=10)
        # Should not raise
        pbar.set_postfix(report="test_report", status="ok")
        pbar.close()

    def test_disabled_bar_can_be_created(self):
        """ProgressBar with disable=True must not raise errors."""
        pbar = ProgressBar(total=10, disable=True)
        pbar.update(1)
        pbar.close()


# ---------------------------------------------------------------------------
# progress_bar() function tests
# ---------------------------------------------------------------------------


class TestProgressBarFunction:
    """Verify progress_bar wraps iterables."""

    def test_progress_bar_wraps_iterable(self):
        """progress_bar must wrap an iterable and yield all items."""
        items = [1, 2, 3, 4, 5]
        result = list(progress_bar(items, desc="Test", disable=True))
        assert result == [1, 2, 3, 4, 5]

    def test_progress_bar_wraps_empty_iterable(self):
        """progress_bar must handle empty iterables."""
        result = list(progress_bar([], desc="Empty", disable=True))
        assert result == []

    def test_progress_bar_wraps_string_iterable(self):
        """progress_bar must work with any iterable type."""
        items = ["a", "b", "c"]
        result = list(progress_bar(items, desc="Strings", unit="char", disable=True))
        assert result == ["a", "b", "c"]

    def test_progress_bar_preserves_order(self):
        """progress_bar must preserve iteration order."""
        items = [10, 20, 30]
        result = list(progress_bar(items, disable=True))
        assert result == [10, 20, 30]


# ---------------------------------------------------------------------------
# create_progress_bar() function tests
# ---------------------------------------------------------------------------


class TestCreateProgressBar:
    """Verify create_progress_bar factory function."""

    def test_creates_progress_bar_instance(self):
        """create_progress_bar must return a ProgressBar instance."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = create_progress_bar(total=10)
        assert isinstance(pbar, ProgressBar)
        pbar.close()

    def test_creates_with_custom_parameters(self):
        """create_progress_bar must pass parameters to ProgressBar."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = create_progress_bar(total=50, desc="Building", unit="module", colour="red")
        assert pbar.pbar.total == 50
        assert pbar.pbar.desc == "Building"
        assert pbar.pbar.unit == "module"
        assert pbar.pbar.colour == "red"
        pbar.close()

    def test_creates_with_default_colour(self):
        """create_progress_bar must default to green colour."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = create_progress_bar(total=10)
        assert pbar.pbar.colour == "green"
        pbar.close()

    def test_creates_usable_as_context_manager(self):
        """create_progress_bar result must be usable as context manager."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            with create_progress_bar(total=5) as pbar:
                for _ in range(5):
                    pbar.update(1)
                assert pbar.pbar.n == 5


# ---------------------------------------------------------------------------
# ReportProgress tests
# ---------------------------------------------------------------------------


class TestReportProgress:
    """Verify specialized report progress tracking."""

    def test_mapping_progress_creates_correct_bar(self):
        """ReportProgress.mapping_progress must create bar with correct settings."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ReportProgress.mapping_progress(total=10)
        assert isinstance(pbar, ProgressBar)
        assert pbar.pbar.total == 10
        assert pbar.pbar.desc == "Mapping reports"
        assert pbar.pbar.unit == "report"
        assert pbar.pbar.colour == "blue"
        pbar.close()

    def test_field_progress_includes_report_name(self):
        """ReportProgress.field_progress must include report name in description."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ReportProgress.field_progress(total=20, report_name="Sales Order")
        assert isinstance(pbar, ProgressBar)
        assert pbar.pbar.total == 20
        assert "Sales Order" in pbar.pbar.desc
        assert pbar.pbar.unit == "field"
        assert pbar.pbar.colour == "cyan"
        pbar.close()

    def test_field_progress_description_format(self):
        """ReportProgress.field_progress must format description as 'Mapping fields for <name>'."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ReportProgress.field_progress(total=5, report_name="Invoice")
        assert pbar.pbar.desc == "Mapping fields for Invoice"
        pbar.close()

    def test_testing_progress_creates_correct_bar(self):
        """ReportProgress.testing_progress must create bar with correct settings."""
        with patch("odoo_fast_report_mapper.progress.sys.stdout", _devnull):
            pbar = ReportProgress.testing_progress(total=8)
        assert isinstance(pbar, ProgressBar)
        assert pbar.pbar.total == 8
        assert pbar.pbar.desc == "Testing reports"
        assert pbar.pbar.unit == "report"
        assert pbar.pbar.colour == "green"
        pbar.close()

    def test_mapping_progress_disabled(self):
        """ReportProgress.mapping_progress must respect disable flag."""
        pbar = ReportProgress.mapping_progress(total=5, disable=True)
        assert pbar.pbar.disable is True
        pbar.close()

    def test_testing_progress_disabled(self):
        """ReportProgress.testing_progress must respect disable flag."""
        pbar = ReportProgress.testing_progress(total=5, disable=True)
        assert pbar.pbar.disable is True
        pbar.close()
