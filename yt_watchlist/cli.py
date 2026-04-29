from __future__ import annotations

from pathlib import Path

import click

from common.io import JsonlEmitter
from yt_watchlist.service import WatchlistConfig, WatchlistService


@click.group()
def cli() -> None:
    """Fetch YouTube Watch Later items as JSONL."""


@cli.command("list")
@click.option("--format", "output_format", type=click.Choice(["jsonl"]), default="jsonl", show_default=True)
@click.option("--limit", type=int, default=None)
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=None)
@click.option(
    "--browser",
    type=click.Choice(["chrome", "chromium", "brave", "edge", "firefox", "safari"], case_sensitive=False),
    default="chrome",
    show_default=True,
)
@click.option("--browser-profile", default=None, help="Optional browser profile name or path for yt-dlp cookie extraction.")
def list_watchlist(
    output_format: str,
    limit: int | None,
    output_path: Path | None,
    browser: str,
    browser_profile: str | None,
) -> None:
    del output_format
    try:
        service = WatchlistService(
            WatchlistConfig(
                browser=browser.lower(),
                browser_profile=browser_profile,
                limit=limit,
            )
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    with JsonlEmitter(mirror_path=output_path) as emitter:
        try:
            for record in service.iter_watchlist():
                emitter.emit(record)
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc
