"""Entry point shim for the optional Twente Milieu CLI.

Kept as a standalone module so the console script remains importable
regardless of whether the ``cli`` extra is installed: if the CLI
dependencies (``typer``, ``rich``) are missing we raise a friendly
``SystemExit`` with an install hint instead of a bare ``ImportError``.
"""

from __future__ import annotations


def main() -> None:
    """Invoke the Typer CLI with a graceful error if extras are missing."""
    try:
        # Deferred import so the console script remains importable even
        # when the optional ``cli`` extra is not installed.
        # pylint: disable-next=import-outside-toplevel
        from twentemilieu.cli import cli  # noqa: PLC0415
    except ModuleNotFoundError as err:  # pragma: no cover
        msg = (
            "The Twente Milieu CLI requires the 'cli' extra. "
            "Install it with: pip install 'twentemilieu[cli]'"
        )
        raise SystemExit(msg) from err
    cli()
