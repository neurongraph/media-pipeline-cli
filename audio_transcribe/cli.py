from __future__ import annotations

from pathlib import Path

import click

from audio_transcribe.whisper_engine import WhisperConfig, WhisperEngine, resolve_device
from common.io import JsonlEmitter, iter_jsonl


@click.command()
@click.option("--input", "input_path", type=click.Path(exists=True, path_type=Path), default=None)
@click.option(
    "--model",
    "model_name",
    type=click.Choice(["tiny", "base", "small", "medium", "large"]),
    default="base",
    show_default=True,
)
@click.option(
    "--device",
    type=click.Choice(["auto", "cpu", "cuda"]),
    default="auto",
    show_default=True,
)
@click.option("--language", default="auto", show_default=True)
@click.option(
    "--output-format",
    type=click.Choice(["json", "text"]),
    default="json",
    show_default=True,
)
@click.option("--cache-dir", type=click.Path(path_type=Path), default=None)
@click.option("--force", is_flag=True, default=False)
def cli(
    input_path: Path | None,
    model_name: str,
    device: str,
    language: str,
    output_format: str,
    cache_dir: Path | None,
    force: bool,
) -> None:
    try:
        engine = WhisperEngine(
            WhisperConfig(
                model_name=model_name,
                device=resolve_device(device),
                language=language,
                output_format=output_format,
                cache_dir=cache_dir,
                force=force,
            )
        )
        records = iter_jsonl(input_path)
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    with JsonlEmitter() as emitter:
        try:
            for record in records:
                emitter.emit(engine.process_record(record))
        except Exception as exc:
            raise click.ClickException(str(exc)) from exc
