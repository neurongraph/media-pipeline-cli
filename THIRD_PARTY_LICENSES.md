# Third-Party Licenses

This project depends on several third-party Python packages. The project itself is licensed under Apache 2.0, but these dependencies remain under their own respective licenses.

## Direct Dependencies

### `click`

- Package: `click`
- Version used locally during development: `8.3.3`
- License: BSD 3-Clause
- Homepage: <https://palletsprojects.com/p/click/>
- Source: <https://github.com/pallets/click>

### `yt-dlp`

- Package: `yt-dlp`
- Version used locally during development: `2026.3.17`
- License: The Unlicense
- Homepage: <https://github.com/yt-dlp/yt-dlp>
- Source: <https://github.com/yt-dlp/yt-dlp>

### `openai-whisper`

- Package: `openai-whisper`
- Version used locally during development: `20250625`
- License: MIT
- Homepage: <https://github.com/openai/whisper>
- Source: <https://github.com/openai/whisper>

## Important Note

Additional transitive dependencies are installed as part of the Python environment, including packages such as `torch`, `tiktoken`, `numpy`, and others. Those packages are distributed under their own licenses.

If you redistribute this project in a packaged form, you should review the installed dependency set in your release environment and ensure that the relevant third-party notices are preserved where required.

## How to Inspect Installed Licenses

To inspect installed dependency metadata locally:

```bash
uv run python - <<'PY'
from importlib.metadata import metadata

for name in ["click", "yt-dlp", "openai-whisper", "torch", "tiktoken"]:
    m = metadata(name)
    print(name)
    print("Version:", m.get("Version"))
    print("License:", m.get("License"))
    print()
PY
```

To inspect license files from the local virtual environment:

```bash
find .venv/lib -path '*/site-packages/*.dist-info/licenses/*' -o -path '*/site-packages/*/LICENSE*'
```
