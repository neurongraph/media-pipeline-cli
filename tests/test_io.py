import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from common.io import JsonlEmitter, iter_jsonl


class IoTests(unittest.TestCase):
    def test_iter_jsonl_reads_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source = Path(tmp_dir) / "input.jsonl"
            source.write_text('{"video_id":"abc"}\n{"video_id":"def"}\n', encoding="utf-8")

            records = list(iter_jsonl(source))

        self.assertEqual(records, [{"video_id": "abc"}, {"video_id": "def"}])

    def test_jsonl_emitter_mirrors_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "output.jsonl"
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                with JsonlEmitter(mirror_path=target) as emitter:
                    emitter.emit({"video_id": "abc"})

            self.assertIn('{"video_id": "abc"}', stdout.getvalue())
            self.assertIn('{"video_id": "abc"}', target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
