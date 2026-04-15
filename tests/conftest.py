"""Shared fixtures and helpers for the test suite."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from twentemilieu import WasteType

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
