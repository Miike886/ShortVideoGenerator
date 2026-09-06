# Reusable character presenter slice

- **Date:** 2026-09-06
- **Status:** Completed with offline and live real-provider runs
- **Branch:** `publish-current-files-20260905`

## Objective

Add a reusable original presenter/mascot to the video pipeline without generating character
images during normal production. The slice proves that scene planning, narration timing,
visual assets, reusable presenter PNGs, subtitles, FFmpeg composition, validation, and review
can run end to end through the existing modular pipeline.

## Scope

The default deterministic script now includes Byte presenter instructions in two scenes:
`explaining` at `bottom_right` and `happy` at `bottom_left`. Scene two intentionally has no
presenter so presenter data remains optional per scene.

Character image generation is out of scope. The production path only loads existing project
assets from `assets/characters/byte/`.

## Architecture

- `CharacterDefinition`, `PresenterInstruction`, and `CharacterAssetReference` are
  project-owned contracts.
- `LocalCharacterAssetProvider` resolves `character.yaml`, validates declared poses, verifies
  PNG/RGBA dimensions, and returns deterministic fingerprints based on provider version,
  character version, definition content, pose content, layout, and motion settings.
- `NarratedMediaWorkflow` runs a `resolve_presenters` step after timeline planning and before
  visual acquisition. It stores `presenters.json` as a production artifact that references
  shared character assets instead of copying PNGs into each production.
- `FfmpegRenderer` overlays presenter PNG inputs on top of each scene background before concat,
  then burns subtitles into the final 1080 x 1920 H.264/AAC MP4.
- Bootstrap wires the local character provider from the composition root. Pipeline modules
  depend only on provider ports and contracts.

## CharacterDefinition

Byte is defined at `assets/characters/byte/character.yaml` with version `byte-v1`, default pose
`neutral`, preferred position `bottom_right`, and 12 available poses:

```text
neutral, explaining, pointing_left, pointing_right, thinking, surprised, happy, laughing,
skeptical, shrugging, working, idea
```

Every declared pose has a transparent PNG asset in the same directory.

## Composition

The presenter occupies roughly 30-32% of frame height in the current deterministic plan and is
placed above the subtitle safe area. The first motion implementation uses alpha fade-in and
fade-out per scene. More expressive movement is intentionally deferred.

## Idempotency

Presenter fingerprints include character id, pose, character version, definition hash, pose
asset hash, position, scale, entrance, and exit configuration. The render request includes
presenter references, so changing a pose file or `character.yaml` changes the final render
inputs.

An idempotent rerun of a completed production returns the same run and production IDs and marks
StepRuns as reused without re-rendering.

## Configuration

`.env.example` documents:

```dotenv
DEFAULT_CHARACTER_ID=byte
```

`DEFAULT_CHARACTER_ID` is used by the deterministic editorial provider when building presenter
instructions. Tests inject `LocalCharacterAssetProvider` and do not call any external API.

## Adding Characters and Poses

To add another character, create `assets/characters/<id>/character.yaml` with its version,
default pose, available poses, preferred position, scale, and local PNG files. Then set
`DEFAULT_CHARACTER_ID=<id>` for manual runs.

To add another pose to Byte, add `<pose>.png` under `assets/characters/byte/`, list it in
`available_poses`, and bump `version` if the visual contract should invalidate previous
fingerprints.

## Validation

- `uv run ruff check .` passed.
- `uv run pytest` passed 35 tests.
- `tests/integration/test_vertical_slice.py` passed with fake TTS, fake visual assets,
  `LocalCharacterAssetProvider`, FFmpeg rendering, ffprobe validation, presenter references,
  and idempotent rerun.
- A manual offline run with fake TTS and fake visual assets produced production
  `00dbbee8-6b49-46e4-98bd-58d26ac2a6f1` in `awaiting_review`.
- Repeating the same idempotency key reused run
  `f618b175-9b3b-44ea-83a2-61dc0ac268b8` and marked all 13 StepRuns as reused.
- `ffprobe` inspected `storage/renders/00dbbee8-6b49-46e4-98bd-58d26ac2a6f1/final.mp4` as
  H.264/AAC, 1080 x 1920, 30 fps, and 15.36 seconds.
- A live real-provider run with Edge TTS and Pexels produced production
  `474928ac-ed9b-4e9b-96f1-05d1234b421c` in `awaiting_review`.
- Repeating the real-provider idempotency key reused run
  `f5214c48-d763-4e5f-bba4-3b001ee72062` and marked all 13 StepRuns as reused.
- The real run selected Pexels assets `8126500`, `12896413`, and `33191904`; used Byte poses
  `explaining` and `happy`; and produced 20.04 seconds of Edge TTS narration.
- `ffprobe` inspected `storage/renders/474928ac-ed9b-4e9b-96f1-05d1234b421c/final.mp4` as
  H.264/AAC, 1080 x 1920, 30 fps, and 20.04 seconds.

## Known Limitations

- No image-generation API is implemented or called for character creation.
- No lip sync, avatar video, skeletal animation, forced subtitle alignment, LLM scene planning,
  social publishing, voice cloning, or multi-character dialogue is included.
- Presenter motion is limited to fade-in/fade-out; subtle translation or scale animation is a
  future enhancement.
- Live Pexels + Edge TTS execution requires explicit operator authorization because it uses
  credentials and contacts external services.
