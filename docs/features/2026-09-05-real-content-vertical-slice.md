# Real-content vertical slice

- **Date:** 2026-09-05
- **Status:** Completed; Pexels live run pending API key
- **Branch:** `feat/deterministic-vertical-slice`

## Objective

Turn a configurable topic and language into an intelligibly narrated vertical video while
keeping every external integration replaceable and preserving an offline, deterministic test
path. The production still ends in human review and never publishes automatically.

## Architecture and providers

- `ManualProductionInput` owns topic, language, and optional target duration.
- The deterministic editorial provider creates a validated brief and a three-scene script;
  every scene includes narration, on-screen text, and a `visual_query`.
- `TextToSpeechProvider` exposes a small project-owned contract. `edge` produces MP3 speech;
  `fake` produces reproducible WAV audio for tests.
- `AssetProvider` returns project-owned metadata. `pexels` searches portrait video first,
  then landscape video and portrait images; `fake` creates deterministic local PPM images.
- The composition root selects adapters from CLI arguments or environment configuration.
  Domain and pipeline modules do not import Edge TTS, Pexels, FastAPI, or SQLAlchemy.
- Temporary downloads and FFmpeg work files remain under `storage/work`; registered final
  artifacts live under `storage/assets` and `storage/renders`.

Pexels assets record provider version, source URL, creator, dimensions, external identifier,
media kind, orientation, query, and attribution text. A query with no remote result is retried
in simplified form and then falls back to the deterministic local provider. Transport,
authentication, and malformed-response errors remain visible instead of being disguised as
successful downloads.

## Executable flow

```text
topic + language
  -> fixture candidate -> evaluate -> select exactly one
  -> brief -> three-scene script with visual queries
  -> TTS -> ffprobe duration
  -> word-weighted scene timeline
  -> one visual asset per scene -> subtitles
  -> FFmpeg render -> ffprobe validation
  -> awaiting_review
```

Images are looped for their scene interval. Video clips are looped when necessary. Both are
scaled and center-cropped to 1080 x 1920. FFmpeg emits H.264/AAC at 30 fps, burns basic SRT
subtitles, and keeps final duration aligned with the narration.

## Configuration

The supported environment values are shown in `.env.example`:

```dotenv
TTS_PROVIDER=edge
TTS_VOICE=en-US-AriaNeural
TTS_RATE=0
TTS_VOLUME=100
ASSET_PROVIDER=pexels
PEXELS_API_KEY=
```

CLI values override settings. `PEXELS_API_KEY` is mandatory only when selecting the Pexels
adapter. Automated tests inject `fake` providers and never contact Edge or Pexels.

## Idempotency

The default idempotency key is derived from normalized input and provider configuration.
Step fingerprints additionally cover narration text, language, TTS options and version,
visual query, asset provider and selection strategy. A matching rerun reuses the same run,
production, StepRuns, artifacts, downloads, audio, and render. Reusing an explicit key with
different inputs is rejected.

## Validation performed

- `uv lock --check`, locked dependency synchronization, Ruff, and `git diff --check` passed.
- The complete offline suite passed 31 tests, including a real FFmpeg/ffprobe integration.
- A live Edge TTS run, using deterministic local visuals because no Pexels key was present,
  produced production `f363dc91-d9ad-43d3-bcc6-9c7788fd61f8` in `awaiting_review`.
- The production has 12 completed StepRuns and eight artifacts. Repeating it returned the
  same IDs and marked every StepRun as reused.
- Edge TTS 7.2.8 produced 16.128 seconds of English narration. `ffprobe` validated a 16.128
  second MP4 with H.264 video, AAC audio, 1080 x 1920 resolution, and 30 fps.
- Pexels parsing, selection, metadata, and no-result fallback are covered with offline fixture
  tests. A live Pexels request was not executed because `PEXELS_API_KEY` was absent; no live
  result is claimed.
- Two upstream Starlette/AnyIO deprecation warnings remain non-blocking.

## Current limits

- Editorial text is deterministic; no LLM integration is included.
- Asset ranking is intentionally simple and no semantic vision validation is performed.
- Captions are scene-level and use a basic burned-in style; there is no word alignment.
- There is no music, generated imagery, automatic publication, authentication, cloud
  deployment, Redis, Celery, or multi-platform output.
- Edge TTS is free to call without a project API key but requires network access. Pexels uses
  its free API quota and requires compliance with its current attribution and usage terms.
