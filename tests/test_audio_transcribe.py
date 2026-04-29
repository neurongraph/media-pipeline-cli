import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from audio_transcribe.whisper_engine import WhisperConfig, WhisperEngine


class FakeWhisperModel:
    def transcribe(self, audio_path: str, **_kwargs: object) -> dict[str, object]:
        print("Detected language: English")
        return {
            "text": "hello world",
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.0,
                    "text": "hello world",
                }
            ],
        }


class WhisperEngineTests(unittest.TestCase):
    def test_transcribe_redirects_dependency_stdout_to_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_path = Path(tmp_dir) / "sample.wav"
            audio_path.write_bytes(b"fake audio")

            config = WhisperConfig(
                model_name="base",
                device="cpu",
                language="auto",
                output_format="json",
                cache_dir=None,
                force=False,
            )

            with patch.object(WhisperEngine, "_load_model", return_value=FakeWhisperModel()):
                engine = WhisperEngine(config)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = engine.process_record({"audio_path": str(audio_path)})

        self.assertEqual("", stdout.getvalue())
        self.assertIn("Detected language: English", stderr.getvalue())
        self.assertEqual("hello world", result["transcript"])
        self.assertEqual(
            [{"start": 0.0, "end": 1.0, "text": "hello world"}],
            result["segments"],
        )


if __name__ == "__main__":
    unittest.main()
