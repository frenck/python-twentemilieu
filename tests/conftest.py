"""Shared fixtures and helpers for the test suite."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import aiohttp
import pytest
from aioresponses import core as aioresponses_core

from twentemilieu import WasteType

FIXTURES_DIR = Path(__file__).parent / "fixtures"

_PICKUP_KEY_TO_WASTE_TYPE: dict[str, WasteType] = {
    "non_recyclable": WasteType.NON_RECYCLABLE,
    "organic": WasteType.ORGANIC,
    "paper": WasteType.PAPER,
    "packages": WasteType.PACKAGES,
    "tree": WasteType.TREE,
}

AIOHTTP_REQUIRES_STREAM_WRITER = (
    "stream_writer" in aiohttp.ClientResponse.__init__.__code__.co_varnames
)

AIOHTTP_STREAM_WRITER = SimpleNamespace(output_size=0)


class AioresponsesClientResponse(aioresponses_core.ClientResponse):
    """Backwards-compatible ClientResponse for aioresponses."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize and provide a stream_writer for aiohttp 3.14+."""
        kwargs.setdefault("stream_writer", AIOHTTP_STREAM_WRITER)
        super().__init__(*args, **kwargs)


@pytest.fixture(scope="session", autouse=True)
def setup_aioresponses_aiohttp_compat() -> Any:
    """Patch aioresponses ClientResponse for aiohttp compatibility in tests."""
    if not AIOHTTP_REQUIRES_STREAM_WRITER:
        yield
        return

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(aioresponses_core, "ClientResponse", AioresponsesClientResponse)
    yield
    monkeypatch.undo()


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
