# Deterministic executable vertical slice

- **Date:** 2026-09-05
- **Status:** Completed
- **Branch:** `feat/deterministic-vertical-slice`

## Objective

Deliver the first end-to-end local execution from a fixture topic to a technically validated
vertical MP4 in a human review queue, without external APIs or paid providers.

## Delivered behavior

- Added `svg-run-manual` with a configurable idempotency key and explicit FFmpeg paths.
- Creates one fixture niche, source, candidate, brief, and three-scene script.
- Evaluates and selects exactly one candidate with reproducible scores.
- Generates one deterministic PPM image per scene, a reproducible WAV tone, and basic SRT
  subtitles.
- Renders H.264/AAC MP4 at 1080 x 1920 and 30 fps with FFmpeg.
- Validates streams, resolution, frame rate, and duration with `ffprobe`.
- Registers images, audio, subtitles, render, and validation report in SQLite with hashes.
- Persists nine successful `StepRun` records and advances the production to
  `awaiting_review`.
- Exposes review queue, production detail, local artifacts, and all three human decisions
  through FastAPI.
- Coordinates the flow through project-owned ports and state models; SQLAlchemy, FFmpeg,
  subtitles, local storage, and HTTP remain replaceable outer adapters.

## Idempotency and storage

`PipelineRun.idempotency_key` is unique. Repeating a completed command returns the existing
run and production without recreating database rows or artifact records. Each provider writes
into `storage/work/{run_id}`; promoted assets live under `storage/assets/{production_id}` and
the MP4 under `storage/renders/{production_id}`. The work directory is removed after the run.

## Validation performed

- `uv run pytest -q`: 25 passed, including the architecture boundary and real render tests.
- The complete integration rendered and validated a real 30-second MP4.
- Repeating the real CLI returned the same run and production with `reused: true`.
- Real API request returned one `awaiting_review` production with seven registered artifacts
  and a passing validation report.
- `ffprobe` reported H.264, 1080 x 1920, 30/1 fps, and 30.000000 seconds.
- A frame extracted at two seconds was visually inspected and showed the expected vertical
  solid-color scene with readable burned-in subtitles.
- `uv run ruff check .`: all checks passed.
- `git diff --check`: no whitespace errors; Git only reported expected Windows line-ending
  notices.

Two upstream deprecation warnings from Starlette/AnyIO remain non-blocking.

## Known limitations

- Audio is a deterministic test tone, not spoken narration.
- Visual assets are solid-color fixture images.
- Scheduling and worker job claiming remain deferred; this slice is initiated by CLI.
- SQLite schema evolution still uses fresh schema creation rather than migrations.
- The API provides JSON endpoints and local files but no review web interface.
