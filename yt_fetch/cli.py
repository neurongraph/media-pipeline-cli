from __future__ import annotations

from pathlib import Path

import click

from common.io import JsonlEmitter, iter_jsonl
from yt_fetch.downloader import DownloadConfig, Downloader


def _shared_options(func):
    func = click.option("--input", "input_path", type=click.Path(exists=True, path_type=Path), default=None)(func)
    func = click.option("--output-dir", type=click.Path(path_type=Path), default=Path("./data"), show_default=True)(func)
    func = click.option("--format", "media_format", type=str, default=None)(func)
    func = click.option("--parallel", type=int, default=2, show_default=True)(func)
    func = click.option("--cache-dir", type=click.Path(path_type=Path), default=None)(func)
    func = click.option("--force", is_flag=True, default=False)(func)
    return func


@click.group()
def cli() -> None:
    """Download YouTube media from JSONL records."""


@cli.command("audio")
@_shared_options
def audio_command(
    input_path: Path | None,
    output_dir: Path,
    media_format: str | None,
    parallel: int,
    cache_dir: Path | None,
    force: bool,
) -> None:
    _run(
        mode="audio",
        input_path=input_path,
        output_dir=output_dir,
        media_format=media_format or "mp3",
        parallel=parallel,
        cache_dir=cache_dir,
        force=force,
    )


@cli.command("video")
@_shared_options
def video_command(
    input_path: Path | None,
    output_dir: Path,
    media_format: str | None,
    parallel: int,
    cache_dir: Path | None,
    force: bool,
) -> None:
    _run(
        mode="video",
        input_path=input_path,
        output_dir=output_dir,
        media_format=media_format or "mp4",
        parallel=parallel,
        cache_dir=cache_dir,
        force=force,
    )


def _run(
    *,
    mode: str,
    input_path: Path | None,
    output_dir: Path,
    media_format: str,
    parallel: int,
    cache_dir: Path | None,
    force: bool,
) -> None:
    if parallel < 1:
        raise click.ClickException("--parallel must be at least 1.")

    try:
        downloader = Downloader(
            DownloadConfig(
                mode=mode,
                output_dir=output_dir,
                media_format=media_format,
                parallel=parallel,
                cache_dir=cache_dir,
                force=force,
            )
        )
        records = iter_jsonl(input_path)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    with JsonlEmitter() as emitter:
        try:
            for record in downloader.process_records(records):
                emitter.emit(record)
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc
