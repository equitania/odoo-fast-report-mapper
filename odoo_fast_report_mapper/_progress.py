# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Progress bar context manager for long-running operations. Internal use only."""

from __future__ import annotations

import sys
from collections.abc import Iterable
from typing import Any

from tqdm import tqdm


def progress_bar(
    iterable: Iterable[Any],
    desc: str = "Processing",
    unit: str = "item",
    total: int | None = None,
    disable: bool = False,
    colour: str | None = None,
) -> tqdm[Any]:
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
        colour=colour or "green",
        file=sys.stdout,
        dynamic_ncols=True,
    )
