"""Command-line interface for the Twente Milieu API."""

from __future__ import annotations

import json
import sys
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from twentemilieu.exceptions import (
    TwenteMilieuAddressError,
    TwenteMilieuConnectionError,
)
from twentemilieu.twentemilieu import TwenteMilieu, WasteType

from .async_typer import AsyncTyper

if TYPE_CHECKING:
    from datetime import date

cli = AsyncTyper(
    help="Twente Milieu CLI",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

WASTE_TYPE_LABELS: dict[WasteType, str] = {
    WasteType.NON_RECYCLABLE: "Non-recyclable",
    WasteType.ORGANIC: "Organic (GFT)",
    WasteType.PAPER: "Paper",
    WasteType.PACKAGES: "Packages (PMD)",
    WasteType.TREE: "Christmas tree",
}

WASTE_TYPE_JSON_NAMES: dict[WasteType, str] = {
    WasteType.NON_RECYCLABLE: "non_recyclable",
    WasteType.ORGANIC: "organic",
    WasteType.PAPER: "paper",
    WasteType.PACKAGES: "packages",
    WasteType.TREE: "tree",
}


class CliWasteType(StrEnum):
    """Machine-friendly waste type names for CLI options."""

    NON_RECYCLABLE = "non-recyclable"
    ORGANIC = "organic"
    PAPER = "paper"
    PACKAGES = "packages"
    TREE = "tree"


CLI_TO_WASTE_TYPE: dict[CliWasteType, WasteType] = {
    CliWasteType.NON_RECYCLABLE: WasteType.NON_RECYCLABLE,
    CliWasteType.ORGANIC: WasteType.ORGANIC,
    CliWasteType.PAPER: WasteType.PAPER,
    CliWasteType.PACKAGES: WasteType.PACKAGES,
    CliWasteType.TREE: WasteType.TREE,
}

PostCode = Annotated[
    str,
    typer.Option(
        help="Postal code of the address",
        prompt="Postal code",
        show_default=False,
        envvar="TWENTEMILIEU_POST_CODE",
    ),
]
HouseNumber = Annotated[
    int,
    typer.Option(
        help="House number of the address",
        prompt="House number",
        show_default=False,
        envvar="TWENTEMILIEU_HOUSE_NUMBER",
    ),
]
HouseLetter = Annotated[
    str,
    typer.Option(
        help="Optional house letter of the address",
        envvar="TWENTEMILIEU_HOUSE_LETTER",
    ),
]
JsonFlag = Annotated[
    bool,
    typer.Option(
        "--json",
        help="Emit machine-readable JSON output",
    ),
]


@cli.error_handler(TwenteMilieuAddressError)
def address_error_handler(_: TwenteMilieuAddressError) -> None:
    """Handle address errors."""
    message = """
    The provided address could not be found in the Twente Milieu service
    area. Please double-check the postal code and house number (and
    optional house letter) and try again.
    """
    panel = Panel(
        message,
        expand=False,
        title="Address not found",
        border_style="red bold",
    )
    console.print(panel)
    sys.exit(1)


@cli.error_handler(TwenteMilieuConnectionError)
def connection_error_handler(_: TwenteMilieuConnectionError) -> None:
    """Handle connection errors."""
    message = """
    Could not connect to the Twente Milieu API. Please check your
    internet connection and try again.
    """
    panel = Panel(
        message,
        expand=False,
        title="Connection error",
        border_style="red bold",
    )
    console.print(panel)
    sys.exit(1)


async def fetch_pickups(
    post_code: str,
    house_number: int,
    house_letter: str,
) -> dict[WasteType, list[date]]:
    """Fetch the pickup schedule for an address."""
    async with TwenteMilieu(
        post_code=post_code,
        house_number=house_number,
        house_letter=house_letter,
    ) as twente:
        return await twente.update()


def format_address(post_code: str, house_number: int, house_letter: str) -> str:
    """Format an address as a human-readable string."""
    return f"{post_code} {house_number}{house_letter}".strip()


def flatten_pickups(
    pickups_by_type: dict[WasteType, list[date]],
) -> list[tuple[date, WasteType]]:
    """Flatten a per-type pickup schedule into a chronologically sorted list."""
    events = [(d, wt) for wt, dates in pickups_by_type.items() for d in dates]
    events.sort(key=lambda event: event[0])
    return events


def emit_json(payload: object) -> None:
    """Emit a payload as indented JSON on stdout."""
    typer.echo(json.dumps(payload, indent=2))


@cli.command("upcoming")
async def upcoming(
    post_code: PostCode,
    house_number: HouseNumber,
    house_letter: HouseLetter = "",
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-n",
            help="Maximum number of upcoming pickups to show",
            min=1,
        ),
    ] = 5,
    output_json: JsonFlag = False,
) -> None:
    """List the next pickups across all waste types in chronological order."""
    pickups_by_type = await fetch_pickups(post_code, house_number, house_letter)
    events = flatten_pickups(pickups_by_type)[:limit]

    if output_json:
        payload = [
            {
                "date": event_date.isoformat(),
                "waste_type": WASTE_TYPE_JSON_NAMES[waste_type],
            }
            for event_date, waste_type in events
        ]
        emit_json(payload)
        return

    address = format_address(post_code, house_number, house_letter)
    table = Table(title=f"Next {limit} pickups for {address}")
    table.add_column("Date", style="cyan bold")
    table.add_column("Waste type", style="cyan bold")

    if not events:
        table.add_row("—", "No upcoming pickups")
    else:
        for event_date, waste_type in events:
            table.add_row(event_date.isoformat(), WASTE_TYPE_LABELS[waste_type])

    console.print(table)


@cli.command("next")
async def next_pickup(
    post_code: PostCode,
    house_number: HouseNumber,
    house_letter: HouseLetter = "",
    waste_type: Annotated[
        CliWasteType | None,
        typer.Option(
            "--waste-type",
            "-t",
            help="Limit the lookup to a single waste type",
            case_sensitive=False,
        ),
    ] = None,
    output_json: JsonFlag = False,
) -> None:
    """Show the very next pickup, optionally filtered to a specific waste type."""
    pickups_by_type = await fetch_pickups(post_code, house_number, house_letter)

    if waste_type is None:
        events = flatten_pickups(pickups_by_type)
        chosen = events[0] if events else None
    else:
        target = CLI_TO_WASTE_TYPE[waste_type]
        dates = pickups_by_type.get(target, [])
        chosen = (dates[0], target) if dates else None

    if output_json:
        payload = (
            None
            if chosen is None
            else {
                "date": chosen[0].isoformat(),
                "waste_type": WASTE_TYPE_JSON_NAMES[chosen[1]],
            }
        )
        emit_json(payload)
        return

    if chosen is None:
        if waste_type is None:
            console.print("[yellow]No upcoming pickups scheduled.[/yellow]")
        else:
            console.print(
                f"[yellow]No upcoming {waste_type.value} pickup scheduled.[/yellow]"
            )
        return

    event_date, event_type = chosen
    label = WASTE_TYPE_LABELS[event_type]
    console.print(
        f"Next pickup: [cyan bold]{label}[/cyan bold] "
        f"on [cyan bold]{event_date.isoformat()}[/cyan bold]",
    )
