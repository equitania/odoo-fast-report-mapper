# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Progress bar utilities for long-running operations.

Provides progress tracking for report mapping, field processing, and testing operations.
"""

from typing import Optional, Iterable, Any
from tqdm import tqdm
import sys


class ProgressBar:
    """
    Wrapper around tqdm for consistent progress bar styling.

    Provides simple progress tracking with customizable styling and descriptions.
    """

    def __init__(
        self,
        total: Optional[int] = None,
        desc: str = "Processing",
        unit: str = "item",
        disable: bool = False,
        leave: bool = True,
        ncols: Optional[int] = None,
        colour: Optional[str] = None
    ):
        """
        Initialize progress bar.

        Args:
            total: Total number of items to process
            desc: Description text shown before the progress bar
            unit: Unit name (e.g., 'report', 'field', 'test')
            disable: Disable progress bar (useful for quiet mode)
            leave: Keep progress bar after completion
            ncols: Width of progress bar (None = auto)
            colour: Color of progress bar (e.g., 'green', 'blue', 'red')
        """
        self.pbar = tqdm(
            total=total,
            desc=desc,
            unit=unit,
            disable=disable,
            leave=leave,
            ncols=ncols,
            colour=colour or 'green',
            file=sys.stdout,
            dynamic_ncols=True
        )

    def update(self, n: int = 1):
        """
        Update progress by n items.

        Args:
            n: Number of items completed
        """
        self.pbar.update(n)

    def set_description(self, desc: str):
        """
        Update the description text.

        Args:
            desc: New description text
        """
        self.pbar.set_description(desc)

    def set_postfix(self, **kwargs):
        """
        Set postfix (additional info after progress bar).

        Args:
            **kwargs: Key-value pairs to display
        """
        self.pbar.set_postfix(**kwargs)

    def close(self):
        """Close the progress bar."""
        self.pbar.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def progress_bar(
    iterable: Iterable[Any],
    desc: str = "Processing",
    unit: str = "item",
    total: Optional[int] = None,
    disable: bool = False,
    colour: Optional[str] = None
) -> Iterable[Any]:
    """
    Wrap an iterable with a progress bar.

    Args:
        iterable: Iterable to wrap
        desc: Description text
        unit: Unit name
        total: Total items (auto-detected if None)
        disable: Disable progress bar
        colour: Progress bar color

    Yields:
        Items from the iterable

    Example:
        >>> reports = [report1, report2, report3]
        >>> for report in progress_bar(reports, desc="Mapping reports", unit="report"):
        ...     process_report(report)
    """
    return tqdm(
        iterable,
        desc=desc,
        unit=unit,
        total=total,
        disable=disable,
        colour=colour or 'green',
        file=sys.stdout,
        dynamic_ncols=True
    )


def create_progress_bar(
    total: int,
    desc: str = "Processing",
    unit: str = "item",
    disable: bool = False,
    colour: str = "green"
) -> ProgressBar:
    """
    Create a new progress bar instance.

    Args:
        total: Total number of items
        desc: Description text
        unit: Unit name
        disable: Disable progress bar
        colour: Progress bar color

    Returns:
        ProgressBar instance

    Example:
        >>> with create_progress_bar(100, "Processing reports", "report") as pbar:
        ...     for i in range(100):
        ...         # Process item
        ...         pbar.update(1)
    """
    return ProgressBar(
        total=total,
        desc=desc,
        unit=unit,
        disable=disable,
        colour=colour
    )


class ReportProgress:
    """Specialized progress tracking for report operations."""

    @staticmethod
    def mapping_progress(total: int, disable: bool = False) -> ProgressBar:
        """
        Create progress bar for report mapping.

        Args:
            total: Number of reports to map
            disable: Disable progress bar

        Returns:
            ProgressBar instance
        """
        return ProgressBar(
            total=total,
            desc="Mapping reports",
            unit="report",
            disable=disable,
            colour="blue"
        )

    @staticmethod
    def field_progress(total: int, report_name: str, disable: bool = False) -> ProgressBar:
        """
        Create progress bar for field mapping.

        Args:
            total: Number of fields to map
            report_name: Name of the report being processed
            disable: Disable progress bar

        Returns:
            ProgressBar instance
        """
        return ProgressBar(
            total=total,
            desc=f"Mapping fields for {report_name}",
            unit="field",
            disable=disable,
            colour="cyan"
        )

    @staticmethod
    def testing_progress(total: int, disable: bool = False) -> ProgressBar:
        """
        Create progress bar for report testing.

        Args:
            total: Number of reports to test
            disable: Disable progress bar

        Returns:
            ProgressBar instance
        """
        return ProgressBar(
            total=total,
            desc="Testing reports",
            unit="report",
            disable=disable,
            colour="green"
        )
