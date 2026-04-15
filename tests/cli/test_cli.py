"""Tests for the Twente Milieu CLI."""

# pylint: disable=redefined-outer-name
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import click
import pytest
from typer.main import get_command
from typer.testing import CliRunner

from twentemilieu.cli import cli
from twentemilieu.exceptions import (
    TwenteMilieuAddressError,
    TwenteMilieuConnectionError,
)

if TYPE_CHECKING:
    from datetime import date

    from syrupy.assertion import SnapshotAssertion

    from twentemilieu import WasteType


@pytest.fixture(autouse=True)
def stable_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force deterministic Rich rendering for stable snapshots."""
    monkeypatch.setenv("COLUMNS", "100")
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("TERM", "dumb")


@pytest.fixture
def runner() -> CliRunner:
    """Return a CLI runner for invoking the Typer app."""
    return CliRunner()


def mock_twentemilieu_class(
    pickups_data: dict[WasteType, list[date]],
) -> MagicMock:
    """Return a MagicMock that stands in for the TwenteMilieu class."""
    client = AsyncMock()
    client.update.return_value = pickups_data

    instance = AsyncMock()
    instance.__aenter__.return_value = client
    instance.__aexit__.return_value = None

    return MagicMock(return_value=instance)


def invoke(
    runner: CliRunner,
    args: list[str],
    pickups_data: dict[WasteType, list[date]],
) -> tuple[int, str, MagicMock]:
    """Invoke the CLI with a mocked TwenteMilieu class and return the result."""
    mock_cls = mock_twentemilieu_class(pickups_data)
    with patch("twentemilieu.cli.TwenteMilieu", mock_cls):
        result = runner.invoke(cli, args)
    return result.exit_code, result.stdout, mock_cls


def test_cli_structure(snapshot: SnapshotAssertion) -> None:
    """The CLI exposes the expected commands and options.

    Inspects the click Command tree directly rather than snapshotting
    rendered help output (which depends on Rich's terminal width
    detection and is therefore environment-sensitive).
    """
    group = get_command(cli)
    assert isinstance(group, click.Group)
    structure = {
        name: sorted(param.name for param in subcommand.params)
        for name, subcommand in sorted(group.commands.items())
    }
    assert structure == snapshot


def test_upcoming(
    runner: CliRunner,
    sample_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Upcoming command prints a chronologically sorted table."""
    exit_code, output, mock_cls = invoke(
        runner,
        ["upcoming", "--post-code", "7531AT", "--house-number", "148"],
        sample_pickups,
    )
    assert exit_code == 0
    assert output == snapshot
    mock_cls.assert_called_once_with(
        post_code="7531AT",
        house_number=148,
        house_letter="",
    )


def test_upcoming_with_house_letter(
    runner: CliRunner,
    sample_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Upcoming command accepts an optional house letter."""
    exit_code, output, mock_cls = invoke(
        runner,
        [
            "upcoming",
            "--post-code",
            "7531AT",
            "--house-number",
            "148",
            "--house-letter",
            "A",
        ],
        sample_pickups,
    )
    assert exit_code == 0
    assert output == snapshot
    mock_cls.assert_called_once_with(
        post_code="7531AT",
        house_number=148,
        house_letter="A",
    )


def test_upcoming_with_limit(
    runner: CliRunner,
    sample_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Upcoming command honours the --limit option."""
    exit_code, output, _ = invoke(
        runner,
        [
            "upcoming",
            "--post-code",
            "7531AT",
            "--house-number",
            "148",
            "--limit",
            "3",
        ],
        sample_pickups,
    )
    assert exit_code == 0
    assert output == snapshot


def test_upcoming_empty(
    runner: CliRunner,
    empty_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Upcoming command renders a placeholder when the schedule is empty."""
    exit_code, output, _ = invoke(
        runner,
        ["upcoming", "--post-code", "7531AT", "--house-number", "148"],
        empty_pickups,
    )
    assert exit_code == 0
    assert output == snapshot


def test_upcoming_json(
    runner: CliRunner,
    sample_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Upcoming command emits JSON when --json is given."""
    exit_code, output, _ = invoke(
        runner,
        [
            "upcoming",
            "--post-code",
            "7531AT",
            "--house-number",
            "148",
            "--limit",
            "3",
            "--json",
        ],
        sample_pickups,
    )
    assert exit_code == 0
    assert output == snapshot


def test_next(
    runner: CliRunner,
    sample_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Next command shows the single next pickup across all types."""
    exit_code, output, _ = invoke(
        runner,
        ["next", "--post-code", "7531AT", "--house-number", "148"],
        sample_pickups,
    )
    assert exit_code == 0
    assert output == snapshot


def test_next_json(
    runner: CliRunner,
    sample_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Next command emits JSON when --json is given."""
    exit_code, output, _ = invoke(
        runner,
        ["next", "--post-code", "7531AT", "--house-number", "148", "--json"],
        sample_pickups,
    )
    assert exit_code == 0
    assert output == snapshot


def test_next_with_waste_type(
    runner: CliRunner,
    sample_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Next command can be filtered to a specific waste type."""
    exit_code, output, _ = invoke(
        runner,
        [
            "next",
            "--post-code",
            "7531AT",
            "--house-number",
            "148",
            "--waste-type",
            "organic",
        ],
        sample_pickups,
    )
    assert exit_code == 0
    assert output == snapshot


def test_next_with_waste_type_json(
    runner: CliRunner,
    sample_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Next command emits JSON for a specific waste type."""
    exit_code, output, _ = invoke(
        runner,
        [
            "next",
            "--post-code",
            "7531AT",
            "--house-number",
            "148",
            "--waste-type",
            "paper",
            "--json",
        ],
        sample_pickups,
    )
    assert exit_code == 0
    assert output == snapshot


def test_next_none(
    runner: CliRunner,
    empty_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Next command reports when there are no upcoming pickups."""
    exit_code, output, _ = invoke(
        runner,
        ["next", "--post-code", "7531AT", "--house-number", "148"],
        empty_pickups,
    )
    assert exit_code == 0
    assert output == snapshot


def test_next_none_json(
    runner: CliRunner,
    empty_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Next command returns null JSON when there are no upcoming pickups."""
    exit_code, output, _ = invoke(
        runner,
        ["next", "--post-code", "7531AT", "--house-number", "148", "--json"],
        empty_pickups,
    )
    assert exit_code == 0
    assert output == snapshot


def test_next_waste_type_none(
    runner: CliRunner,
    sample_pickups: dict[WasteType, list[date]],
    snapshot: SnapshotAssertion,
) -> None:
    """Next command reports when a specific type has no upcoming pickup."""
    exit_code, output, _ = invoke(
        runner,
        [
            "next",
            "--post-code",
            "7531AT",
            "--house-number",
            "148",
            "--waste-type",
            "tree",
        ],
        sample_pickups,
    )
    assert exit_code == 0
    assert output == snapshot


def test_address_error_handler(
    capsys: pytest.CaptureFixture[str],
    snapshot: SnapshotAssertion,
) -> None:
    """Address error handler prints a panel and exits with 1."""
    handler = cli.error_handlers[TwenteMilieuAddressError]
    with pytest.raises(SystemExit) as exc_info:
        handler(TwenteMilieuAddressError("unknown"))
    assert exc_info.value.code == 1
    assert capsys.readouterr().out == snapshot


def test_connection_error_handler(
    capsys: pytest.CaptureFixture[str],
    snapshot: SnapshotAssertion,
) -> None:
    """Connection error handler prints a panel and exits with 1."""
    handler = cli.error_handlers[TwenteMilieuConnectionError]
    with pytest.raises(SystemExit) as exc_info:
        handler(TwenteMilieuConnectionError("unreachable"))
    assert exc_info.value.code == 1
    assert capsys.readouterr().out == snapshot
