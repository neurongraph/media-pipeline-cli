from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import IO, Any, Iterator


class JsonlEmitter:
    """Writes JSONL records to stdout and optionally mirrors them to a file."""

    def __init__(self, mirror_path: Path | None = None) -> None:
        self._stdout = sys.stdout
        self._mirror: IO[str] | None = None
        if mirror_path is not None:
            mirror_path.parent.mkdir(parents=True, exist_ok=True)
            self._mirror = mirror_path.open("w", encoding="utf-8")

    def emit(self, record: dict[str, Any]) -> None:
        line = json.dumps(record, ensure_ascii=False)
        self._stdout.write(f"{line}\n")
        self._stdout.flush()
        if self._mirror is not None:
            self._mirror.write(f"{line}\n")
            self._mirror.flush()

    def close(self) -> None:
        if self._mirror is not None:
            self._mirror.close()

    def __enter__(self) -> "JsonlEmitter":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def open_input(input_path: Path | None) -> IO[str]:
    if input_path is None:
        return sys.stdin
    return input_path.open("r", encoding="utf-8")


def iter_jsonl(input_path: Path | None) -> Iterator[dict[str, Any]]:
    stream = open_input(input_path)
    should_close = input_path is not None
    try:
        for line_number, raw_line in enumerate(stream, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"Line {line_number} must decode to a JSON object.")
            yield payload
    finally:
        if should_close:
            stream.close()
