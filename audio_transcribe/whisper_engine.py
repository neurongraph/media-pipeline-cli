from __future__ import annotations

import contextlib
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from common.logging import get_logger
from common.schema import Record, merge_fields, should_skip_error, stage_error

logger = get_logger(__name__)


@dataclass(slots=True)
class WhisperConfig:
    model_name: str
    device: str
    language: str
    output_format: str
    cache_dir: Path | None
    force: bool


class WhisperEngine:
    def __init__(self, config: WhisperConfig) -> None:
        self.config = config
        if self.config.cache_dir is not None:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model = self._load_model()

    def _load_model(self):
        import whisper

        logger.info("Loading Whisper model '%s' on %s.", self.config.model_name, self.config.device)
        with self._dependency_stdout_to_stderr():
            return whisper.load_model(self.config.model_name, device=self.config.device)

    def process_record(self, record: Record) -> Record:
        if should_skip_error(record):
            return record

        try:
            return self._transcribe_record(record)
        except Exception as exc:
            logger.exception("Failed to transcribe record.")
            return stage_error(record, "audio-transcribe", str(exc))

    def _transcribe_record(self, record: Record) -> Record:
        if "transcript" in record and not self.config.force:
            return record

        audio_path = record.get("audio_path")
        if not isinstance(audio_path, str) or not audio_path:
            raise ValueError("Record is missing audio_path.")

        source_path = Path(audio_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        cached_payload = self._read_cache(source_path)
        if cached_payload is None:
            with self._dependency_stdout_to_stderr():
                result = self.model.transcribe(
                    str(source_path),
                    language=None if self.config.language == "auto" else self.config.language,
                    verbose=False,
                    fp16=self.config.device == "cuda",
                )
            cached_payload = {
                "transcript": result.get("text", "").strip(),
                "segments": [
                    {
                        "start": float(segment["start"]),
                        "end": float(segment["end"]),
                        "text": segment["text"].strip(),
                    }
                    for segment in result.get("segments", [])
                ],
            }
            self._write_cache(source_path, cached_payload)

        payload = {"transcript": cached_payload["transcript"]}
        if self.config.output_format == "json":
            payload["segments"] = cached_payload["segments"]

        return merge_fields(record, payload, force=self.config.force)

    def _cache_path(self, source_path: Path) -> Path | None:
        if self.config.cache_dir is None:
            return None

        stat = source_path.stat()
        digest = hashlib.sha256(
            f"{source_path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}:{self.config.model_name}:{self.config.language}".encode(
                "utf-8"
            )
        ).hexdigest()
        return self.config.cache_dir / f"{digest}.json"

    def _read_cache(self, source_path: Path) -> dict[str, object] | None:
        if self.config.force:
            return None

        cache_path = self._cache_path(source_path)
        if cache_path is None or not cache_path.exists():
            return None

        return json.loads(cache_path.read_text(encoding="utf-8"))

    def _write_cache(self, source_path: Path, payload: dict[str, object]) -> None:
        cache_path = self._cache_path(source_path)
        if cache_path is None:
            return
        cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    @contextlib.contextmanager
    def _dependency_stdout_to_stderr():
        with contextlib.redirect_stdout(sys.stderr):
            yield


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested

    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"
