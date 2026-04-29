import unittest

from common.schema import merge_fields, stage_error


class SchemaTests(unittest.TestCase):
    def test_merge_fields_preserves_existing_without_force(self) -> None:
        original = {"video_id": "abc123", "title": "keep me"}
        merged = merge_fields(original, {"title": "replace me", "url": "https://example.com"})

        self.assertEqual(merged["title"], "keep me")
        self.assertEqual(merged["url"], "https://example.com")

    def test_merge_fields_overwrites_with_force(self) -> None:
        original = {"transcript": "old"}
        merged = merge_fields(original, {"transcript": "new"}, force=True)

        self.assertEqual(merged["transcript"], "new")

    def test_stage_error_keeps_existing_error_fields(self) -> None:
        record = {"error": "upstream", "stage": "old"}
        errored = stage_error(record, "audio-transcribe", "new error")

        self.assertEqual(errored["error"], "upstream")
        self.assertEqual(errored["stage"], "old")


if __name__ == "__main__":
    unittest.main()
