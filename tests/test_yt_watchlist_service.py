import unittest
from unittest.mock import patch

from yt_watchlist.service import WATCHLIST_URL, WatchlistConfig, WatchlistService


class FakeYoutubeDL:
    last_options = None
    last_url = None
    last_download = None
    result = {
        "entries": [
            {"id": "abc123", "title": "First", "url": "https://www.youtube.com/watch?v=abc123"},
            {"id": "def456", "title": "Second", "url": "def456"},
        ]
    }

    def __init__(self, options):
        FakeYoutubeDL.last_options = options

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        FakeYoutubeDL.last_url = url
        FakeYoutubeDL.last_download = download
        return FakeYoutubeDL.result


class WatchlistServiceTests(unittest.TestCase):
    @patch("yt_watchlist.service.YoutubeDL", FakeYoutubeDL)
    def test_iter_watchlist_emits_jsonl_ready_records(self) -> None:
        service = WatchlistService(
            WatchlistConfig(browser="chrome", browser_profile="Default", limit=2)
        )

        records = list(service.iter_watchlist())

        self.assertEqual(
            FakeYoutubeDL.last_options["cookiesfrombrowser"],
            ("chrome", "Default", None, None),
        )
        self.assertEqual(FakeYoutubeDL.last_options["playlistend"], 2)
        self.assertEqual(records[0]["video_id"], "abc123")
        self.assertEqual(records[0]["url"], "https://www.youtube.com/watch?v=abc123")
        self.assertEqual(records[1]["url"], "https://www.youtube.com/watch?v=def456")
        self.assertEqual(records[1]["source"], "youtube")

    @patch("yt_watchlist.service.YoutubeDL", FakeYoutubeDL)
    def test_service_queries_watch_later_url(self) -> None:
        service = WatchlistService(WatchlistConfig(browser="chrome"))
        list(service.iter_watchlist())
        self.assertEqual(FakeYoutubeDL.last_url, WATCHLIST_URL)
        self.assertFalse(FakeYoutubeDL.last_download)


if __name__ == "__main__":
    unittest.main()
