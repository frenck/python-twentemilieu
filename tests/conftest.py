"""Shared fixtures and helpers for the test suite."""
# pylint: disable=wrong-import-position

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

# Typer caches TERMINAL_WIDTH into typer.rich_utils.MAX_WIDTH at import time,
# so forcing a deterministic width for snapshot tests must happen before typer
# is imported anywhere in the test suite. conftest.py is loaded before any
# test module, so setting it here is guaranteed to run first. We also
# explicitly import typer.rich_utils and overwrite MAX_WIDTH to cover any
# edge case where typer might have been imported before this line runs.
os.environ["TERMINAL_WIDTH"] = "100"

import pytest
import typer.rich_utils

from twentemilieu import WasteType

typer.rich_utils.MAX_WIDTH = 100

FIXTURES_DIR = Path(__file__).parent / "fixtures"

_PICKUP_KEY_TO_WASTE_TYPE: dict[str, WasteType] = {
    "non_recyclable": WasteType.NON_RECYCLABLE,
    "organic": WasteType.ORGANIC,
    "paper": WasteType.PAPER,
    "packages": WasteType.PACKAGES,
    "tree": WasteType.TREE,
}


def load_fixture(filename: str) -> Any:
    """Load a JSON fixture file from the tests/fixtures directory."""
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _parse_pickups(raw: dict[str, list[str]]) -> dict[WasteType, list[date]]:
    """Parse a pickups fixture mapping keys to WasteType and ISO date strings."""
    return {
        _PICKUP_KEY_TO_WASTE_TYPE[key]: [date.fromisoformat(d) for d in dates]
        for key, dates in raw.items()
    }


@pytest.fixture
def calendar_response() -> Any:
    """Return a sample GetCalendar API response payload."""
    return load_fixture("calendar_response.json")


@pytest.fixture
def sample_pickups() -> dict[WasteType, list[date]]:
    """Return a realistic pickup schedule used for CLI rendering tests."""
    return _parse_pickups(load_fixture("sample_pickups.json"))


@pytest.fixture
def empty_pickups() -> dict[WasteType, list[date]]:
    """Return a pickup schedule where every waste type has no upcoming dates."""
    return _parse_pickups(load_fixture("empty_pickups.json"))
