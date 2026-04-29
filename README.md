# media-pipeline-cli

Composable JSONL-streaming CLI tools for YouTube media extraction and local transcription.

## Quick Start: Export YouTube Watch Later URLs

### 1. Install dependencies

From the project root:

```bash
uv sync
```

### 2. Sign into YouTube in Chrome

The `yt-watchlist` command reads the Watch Later playlist through `yt-dlp` using your browser cookies.

Before running it:

1. Open Chrome.
2. Sign into the Google account that owns the target YouTube Watch Later playlist.
3. Confirm that `https://www.youtube.com/playlist?list=WL` shows your Watch Later items in that browser.

### 3. Run the watchlist export

```bash
uv run yt-watchlist list
```

By default, the CLI reads cookies from `chrome`.

If you use another browser:

```bash
uv run yt-watchlist list --browser brave
uv run yt-watchlist list --browser edge
uv run yt-watchlist list --browser firefox
```

If you need a specific browser profile:

```bash
uv run yt-watchlist list --browser chrome --browser-profile "Default"
```

### 4. Save the output to a file

```bash
uv run yt-watchlist list --output watchlist.jsonl
```

Each output line is a JSON object like:

```json
{"video_id":"abc123","title":"Video title","url":"https://www.youtube.com/watch?v=abc123","source":"youtube"}
```

### 5. Test with a small sample

```bash
uv run yt-watchlist list --limit 5
```

### Troubleshooting

- No output: the YouTube Data API does not expose Watch Later items. This CLI uses `yt-dlp` plus browser cookies instead.
- Wrong Watch Later list: sign into the browser profile that owns the target YouTube Watch Later playlist.
- Cookie extraction issues: try `--browser-profile "Default"` for Chrome-based browsers.
- Browser mismatch: if Chrome is not where you are logged in, pass `--browser firefox`, `--browser brave`, or another supported browser.

## YouTube Data API Note

YouTube Data API v3 still works for normal playlists that are accessible to the authenticated caller, including:

- playlists you own
- public playlists
- unlisted playlists you can access
- channel-associated playlists like uploads and likes

It does not return items for the special Watch Later (`WL`) or Watch History (`HL`) playlists.

## Download Media with `yt-fetch`

`yt-fetch` reads JSONL records from stdin or `--input`, downloads media with `yt-dlp`, and emits the original records enriched with `audio_path` or `video_path`.

### Download audio from the watchlist

```bash
uv run yt-watchlist list --limit 5 \
  | uv run yt-fetch audio --output-dir ./data \
  > audio.jsonl
```

You can also read from a file:

```bash
uv run yt-fetch audio --input watchlist.jsonl --output-dir ./data > audio.jsonl
```

Example output record:

```json
{"video_id":"abc123","title":"Video title","url":"https://www.youtube.com/watch?v=abc123","source":"youtube","audio_path":"data/abc123.mp3"}
```

### Download video instead of audio

```bash
uv run yt-fetch video --input watchlist.jsonl --output-dir ./data > video.jsonl
```

Example output record:

```json
{"video_id":"abc123","title":"Video title","url":"https://www.youtube.com/watch?v=abc123","source":"youtube","video_path":"data/abc123.mp4"}
```

### Common `yt-fetch` options

- `--output-dir ./data`: target directory for downloaded files
- `--format mp3|wav|mp4`: output format, defaults to `mp3` for audio and `mp4` for video
- `--parallel 2`: concurrent download workers
- `--cache-dir ./.cache/yt-fetch`: optional yt-dlp cache/archive directory
- `--force`: redownload even if the target file already exists

Examples:

```bash
uv run yt-fetch audio --input watchlist.jsonl --output-dir ./data --format wav
uv run yt-fetch audio --input watchlist.jsonl --output-dir ./data --parallel 4
uv run yt-fetch video --input watchlist.jsonl --output-dir ./data --format mp4
```

### `yt-fetch` behavior

- Output filenames are deterministic: `{video_id}.{ext}`
- Existing files are reused unless `--force` is passed
- Unknown input fields are preserved in the output JSONL
- Per-record failures are emitted back as JSON with `error` and `stage`

## Transcribe Audio with `audio-transcribe`

`audio-transcribe` reads JSONL records that contain `audio_path`, runs local Whisper transcription, and emits the original records enriched with `transcript` and optionally `segments`.

### Transcribe downloaded audio

```bash
uv run audio-transcribe --input audio.jsonl --model base > transcripts.jsonl
```

Or as a pipeline:

```bash
uv run yt-watchlist list --limit 5 \
  | uv run yt-fetch audio --output-dir ./data \
  | uv run audio-transcribe --model base \
  > transcripts.jsonl
```

Example output record:

```json
{"video_id":"abc123","title":"Video title","url":"https://www.youtube.com/watch?v=abc123","source":"youtube","audio_path":"data/abc123.mp3","transcript":"full text...","segments":[{"start":0.0,"end":4.2,"text":"hello"},{"start":4.2,"end":8.1,"text":"world"}]}
```

### Common `audio-transcribe` options

- `--model tiny|base|small|medium|large`: Whisper model size, default `base`
- `--device auto|cpu|cuda`: device selection, default `auto`
- `--language auto|en|...`: optional language hint
- `--output-format json|text`: include segments with `json`, transcript-only with `text`
- `--cache-dir ./.cache/whisper`: optional cache directory for transcript reuse
- `--force`: recompute transcript even if the record already has one

Examples:

```bash
uv run audio-transcribe --input audio.jsonl --model tiny
uv run audio-transcribe --input audio.jsonl --model base --language en
uv run audio-transcribe --input audio.jsonl --model small --device cpu
uv run audio-transcribe --input audio.jsonl --output-format text
```

### `audio-transcribe` behavior

- The Whisper model is loaded once per run
- Timestamps are preserved when `--output-format json` is used
- Cached transcripts can be reused when `--cache-dir` is set
- Unknown input fields are preserved in the output JSONL
- Per-record failures are emitted back as JSON with `error` and `stage`

## End-to-End Pipeline

Fetch Watch Later URLs, download audio, and transcribe locally:

```bash
uv run yt-watchlist list \
  | uv run yt-fetch audio --output-dir ./data \
  | uv run audio-transcribe --model base \
  > transcripts.jsonl
```

Run the stages separately:

```bash
uv run yt-watchlist list --output watchlist.jsonl
uv run yt-fetch audio --input watchlist.jsonl --output-dir ./data > audio.jsonl
uv run audio-transcribe --input audio.jsonl --model base > transcripts.jsonl
```

## JSONL Contract

Each stage preserves upstream fields and appends new ones.

Watchlist records:

```json
{"video_id":"abc123","title":"Video title","url":"https://www.youtube.com/watch?v=abc123","source":"youtube"}
```

After audio download:

```json
{"video_id":"abc123","title":"Video title","url":"https://www.youtube.com/watch?v=abc123","source":"youtube","audio_path":"data/abc123.mp3"}
```

After transcription:

```json
{"video_id":"abc123","title":"Video title","url":"https://www.youtube.com/watch?v=abc123","source":"youtube","audio_path":"data/abc123.mp3","transcript":"full text...","segments":[{"start":0.0,"end":4.2,"text":"hello"}]}
```

Failure records keep the original fields and add:

```json
{"video_id":"abc123","url":"https://www.youtube.com/watch?v=abc123","error":"message","stage":"yt-fetch"}
```

## Install as a CLI Tool

This project defines console entry points for:

- `yt-watchlist`
- `yt-fetch`
- `audio-transcribe`

You can run them with `uv run ...` from the repo, or install them as top-level CLI tools.

### Install from the local repo

From the project root:

```bash
uv tool install .
```

That installs the package and exposes the CLI commands globally in your user tool environment.

If you update the repo later:

```bash
uv tool upgrade --from . media-pipeline-cli
```

### Install directly from GitHub

Once the repository is public, you can install it without cloning first:

```bash
uv tool install git+https://github.com/neurongraph/media-pipeline-cli-tools.git
```

### Alternative: `pipx`

If you prefer `pipx`:

```bash
pipx install .
```

## Build and Package

Build the distributable artifacts from the project root:

```bash
uv build
```

This produces standard Python package artifacts in `dist/`, typically:

- a source distribution (`.tar.gz`)
- a wheel (`.whl`)

These artifacts can be installed locally for validation:

```bash
uv tool install dist/*.whl
```

## Publish to PyPI

When you are ready to publish:

```bash
uv publish
```

Typical release flow:

1. Update the version in `pyproject.toml`
2. Run `uv sync`
3. Run validation checks
4. Build with `uv build`
5. Publish with `uv publish`

After publishing, users can install the CLI directly from PyPI:

```bash
uv tool install media-pipeline-cli
```

## Packaging Notes

- Project metadata and CLI entry points are defined in [pyproject.toml](/Users/surjitdas/projects/media-pipeline-cli/pyproject.toml)
- The package is built with `hatchling`
- Wheel packaging is configured explicitly because the repo contains multiple top-level Python packages
- `uv sync` prepares the local environment, while `uv tool install` installs the package as a reusable CLI
