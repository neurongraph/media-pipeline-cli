from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import parse_qs, urlparse

from yt_dlp import YoutubeDL

from common.logging import get_logger
from common.schema import Record, merge_fields, should_skip_error, stage_error

logger = get_logger(__name__)


@dataclass(slots=True)
class DownloadConfig:
    mode: str
    output_dir: Path
    media_format: str
    parallel: int
    cache_dir: Path | None
    force: bool


class Downloader:
    def __init__(self, config: DownloadConfig) -> None:
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        if self.config.cache_dir is not None:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)

    def process_records(self, records: Iterable[Record]) -> Iterator[Record]:
        with ThreadPoolExecutor(max_workers=self.config.parallel) as executor:
            for result in executor.map(self.process_record, records):
                yield result

    def process_record(self, record: Record) -> Record:
        if should_skip_error(record):
            return record

        try:
            return self._download_record(record)
        except Exception as exc:
            logger.exception("Failed to process record for yt-fetch.")
            return stage_error(record, "yt-fetch", str(exc))

    def _download_record(self, record: Record) -> Record:
        field_name = "audio_path" if self.config.mode == "audio" else "video_path"
        if field_name in record and not self.config.force:
            return record

        video_id = resolve_video_id(record)
        if not video_id:
            raise ValueError("Record is missing video_id and URL does not contain a video identifier.")

        source_url = record.get("url") or f"https://www.youtube.com/watch?v={video_id}"
        target_path = self.config.output_dir / f"{video_id}.{self.config.media_format}"

        if target_path.exists() and not self.config.force:
            return merge_fields(record, {field_name: str(target_path)})

        ydl_options = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "outtmpl": str(self.config.output_dir / f"{video_id}.%(ext)s"),
            "overwrites": self.config.force,
        }

        if self.config.cache_dir is not None:
            ydl_options["cachedir"] = str(self.config.cache_dir)
            ydl_options["download_archive"] = str(self.config.cache_dir / f"{self.config.mode}.archive")
        else:
            ydl_options["cachedir"] = False

        if self.config.mode == "audio":
            ydl_options.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": self.config.media_format,
                        }
                    ],
                }
            )
        else:
            ydl_options.update(
                {
                    "format": "bv*+ba/b",
                    "merge_output_format": self.config.media_format,
                }
            )

        with YoutubeDL(ydl_options) as downloader:
            downloader.download([source_url])

        if not target_path.exists():
            matches = sorted(self.config.output_dir.glob(f"{video_id}.*"))
            if not matches:
                raise FileNotFoundError(f"Download completed but {target_path} was not created.")
            target_path = matches[0]

        return merge_fields(record, {field_name: str(target_path)}, force=self.config.force)


def resolve_video_id(record: Record) -> str:
    video_id = record.get("video_id")
    if isinstance(video_id, str) and video_id:
        return video_id

    url = record.get("url")
    if not isinstance(url, str) or not url:
        return ""

    parsed = urlparse(url)
    if parsed.netloc.endswith("youtu.be"):
        return parsed.path.lstrip("/")
    query = parse_qs(parsed.query)
    return query.get("v", [""])[0]
