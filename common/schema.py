from __future__ import annotations

from typing import Any

Record = dict[str, Any]

AUDIO_FIELD = "audio_path"
VIDEO_FIELD = "video_path"
TRANSCRIPT_FIELD = "transcript"


def merge_fields(record: Record, additions: Record, *, force: bool = False) -> Record:
    merged = dict(record)
    for key, value in additions.items():
        if force or key not in merged:
            merged[key] = value
    return merged


def stage_error(record: Record, stage: str, message: str) -> Record:
    error_record = dict(record)
    error_record.setdefault("error", message)
    error_record.setdefault("stage", stage)
    return error_record


def should_skip_error(record: Record) -> bool:
    return bool(record.get("error"))
