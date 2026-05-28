# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Tests for odoo_fast_report_mapper/_progress.py - progress_bar function only.

The dead public APIs (ProgressBar class, create_progress_bar, ReportProgress)
have been removed as part of Phase 1 consolidation (DEAD-01/DEAD-02/DEAD-03).
"""

from odoo_fast_report_mapper._progress import progress_bar


# ---------------------------------------------------------------------------
# TestProgressBarFunction — the only surviving test class (DEAD-04 excluded)
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
