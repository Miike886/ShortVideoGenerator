# Structured content and dynamic captions

- **Date:** 2026-09-06
- **Status:** Completed with fake alignment; WhisperX adapter isolated but not executed
- **Branch:** `publish-current-files-20260905`

## Objective

Move the generated short away from a technical demo by combining structured informative
content, Byte in every scene, narration, word timestamps, progressive captions, Pexels
visuals, FFmpeg rendering, validation, and review.

## Delivered Behavior

- The deterministic editorial provider now emits five ordered scenes with roles:
  `hook`, `context`, `fact`, `development`, and `conclusion`.
- Scene narration follows an informative progression rather than a hook-only sequence.
- Byte is present in every generated scene by default with deterministic role-based pose,
  position, and scale choices.
- `PresenterInstruction.visibility` can explicitly hide Byte for a scene, but missing
  presenter configuration defaults to the configured character.
- Missing poses fall back deterministically to the character default pose and record the
  fallback reason in the character reference.
- Caption alignment is behind `CaptionAlignmentProvider`.
- The fake alignment provider uses known script text and real audio duration to create fast,
  deterministic word timestamps for tests and offline/manual runs.
- A WhisperX provider shell exists behind the same port. It is optional and intentionally
  isolated from domain, pipeline, tests, and provider ports.
- Dynamic captions render as `.ass` through FFmpeg/libass with 2-5 word groups and active-word
  color emphasis.

## Architecture

`CaptionAlignmentProvider` is a small provider port. The pipeline passes the persisted
narration audio path, validated script, and observed audio duration into the provider and
stores the result as `alignment.json` with ArtifactType `caption_alignment`.

`AssSubtitleProvider` converts `WordTiming` values into deterministic caption groups and
generates `subtitles.ass`. Styling lives in `CaptionStyle`, not in FFmpeg filter strings.
FFmpeg only overlays Byte, concatenates scenes, burns the ASS subtitles, and maps narration.

WhisperX does not leak into contracts, domain, pipeline, persistence, or tests. The optional
adapter imports it only inside `WhisperXCaptionAlignmentProvider.align`.

## Idempotency

Caption alignment fingerprints include narration audio hash, known script text, provider, and
provider version. Subtitle fingerprints include alignment hash, word timings, subtitle
provider, and provider version. Render fingerprints include script data and all non-render
artifact hashes/metadata, so changing captions, alignment, presenter references, visual assets,
or narration invalidates the final render.

## Manual Execution

The existing command remains the entry point:

```powershell
uv run svg-run-manual --topic "Why structured captions make short videos easier to follow" --language en
```

Configuration:

```dotenv
CAPTION_ALIGNMENT_PROVIDER=fake
WHISPERX_MODEL=small
WHISPERX_DEVICE=cpu
```

Set `CAPTION_ALIGNMENT_PROVIDER=whisperx` only after installing and wiring the local WhisperX
runtime. Automated tests use the fake provider and never download models or access the
internet.

## Validation

- `uv run pytest tests/unit/test_dynamic_captions.py tests/unit/test_presenter_planning.py
  tests/unit/test_character_assets.py tests/unit/test_narrated_timeline.py
  tests/integration/test_vertical_slice.py` passed 10 tests.
- Manual real-provider run with Edge TTS, Pexels, Byte, ASS captions, and fake alignment
  produced production `3798ea28-cab0-4f54-8a47-c1a5d10246f8` in `awaiting_review`.
- The manual run completed 14 StepRuns and registered 12 artifacts.
- The structured script contained five scenes with Byte present in every scene.
- Byte poses used: `explaining`, `thinking`, `surprised`, `pointing_left`, `happy`.
- Edge TTS generated 35.016 seconds of narration.
- Fake alignment produced 95 word timings and ASS generation produced 32 caption groups with
  active-word emphasis enabled.
- Pexels assets selected: `38410501`, `10145286`, `38410501`, `13929660`, and `38410501`.
- `ffprobe` inspected `storage/renders/3798ea28-cab0-4f54-8a47-c1a5d10246f8/final.mp4` as
  H.264/AAC, 1080 x 1920, 30 fps, and 35.0 seconds.
- Repeating idempotency key `structured-dynamic-captions-real-v2` reused run
  `eda4ad8a-cb82-4184-b629-70be37af8155`.

## Known Limitations

- WhisperX was not executed because it is not installed in the current local environment.
- The WhisperX adapter currently preserves the architectural boundary and reports a clear
  runtime limitation until model loading/alignment is wired in an environment with WhisperX.
- Caption styling is intentionally simple; the slice prioritizes timing correctness,
  progressive groups, and active-word emphasis over elaborate kinetic typography.
- No lip sync, avatar generation, image-generation API, paid caption API, voice cloning,
  social publishing, or multi-character dialogue is included.
