from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from common.logging import get_logger

try:
    from yt_dlp import YoutubeDL
except ModuleNotFoundError:  # pragma: no cover - exercised only outside the managed env
    YoutubeDL = None

WATCHLIST_URL = "https://www.youtube.com/playlist?list=WL"

logger = get_logger(__name__)


@dataclass(slots=True)
class WatchlistConfig:
    browser: str
    browser_profile: str | None = None
    limit: int | None = None


class WatchlistService:
    def __init__(self, config: WatchlistConfig) -> None:
        self.config = config

    def iter_watchlist(self) -> Iterator[dict[str, str]]:
        if YoutubeDL is None:
            raise ModuleNotFoundError(
                "yt-dlp is not installed in the active Python environment. Run `uv sync` first."
            )

        options = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "lazy_playlist": True,
            "playlistend": self.config.limit,
            "cookiesfrombrowser": (
                self.config.browser,
                self.config.browser_profile,
                None,
                None,
            ),
        }

        logger.info(
            "Loading Watch Later via yt-dlp using browser cookies from %s%s.",
            self.config.browser,
            f" (profile: {self.config.browser_profile})" if self.config.browser_profile else "",
        )

        with YoutubeDL(options) as ydl:
            result = ydl.extract_info(WATCHLIST_URL, download=False)

        entries = result.get("entries", []) if isinstance(result, dict) else []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            video_id = str(entry.get("id") or "").strip()
            if not video_id:
                logger.warning("Skipping watchlist entry without a video ID.")
                continue

            title = str(entry.get("title") or "").strip()
            webpage_url = str(entry.get("url") or "").strip()
            if not webpage_url.startswith("http"):
                webpage_url = f"https://www.youtube.com/watch?v={video_id}"

            yield {
                "video_id": video_id,
                "title": title,
                "url": webpage_url,
                "source": "youtube",
            }
