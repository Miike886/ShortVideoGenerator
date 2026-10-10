# Development changelog

This changelog records meaningful product and architecture changes. Detailed context lives
in the linked records under `docs/features/`.

## 2026-10-10

### Added

- Advisory CodeRabbit configuration with incremental reviews and project-specific review
  instructions; manual review verified on PR #8, with service-side automatic-review limits.
- Risk-appropriate feature tests and local mini-review before PR publication in `AGENTS.md`.

### Validated

- CodeRabbit completed its initial review with two minor findings, corrected by disabling
  commit-count pausing and clarifying risk-appropriate tests; follow-up remote review pending.
- Publication checks passed: 56 tests with FFmpeg integration, architecture boundaries,
  Ruff, lockfile and Git whitespace checks; two upstream deprecation warnings remain.
- Re-rendered a local preview using cached real narration, Pexels clips and Byte assets;
  ffprobe validated H.264/AAC portrait output. No new full production was executed.
- Clarified the fixed five-scene planner and the structural-only Editorial Gate limitations
  in the feature records.

## 2026-09-06

### Added

- Persisted `editorial_gate` step that validates semantic stories and stops failed
  productions before narration generation.
- Semantic story plans with central claims, scene responsibilities, redundancy diagnostics,
  concrete visual concepts and observable-action search planning.
- Semantic scene visual directions, persisted visual plans, deterministic Byte choreography,
  focal-safe placement, normalized beats, reframing motion, and ranked Pexels candidates.
- Credit-safe `TTS_MODE=live|cached` policy, cache integrity checks, TTS request observability,
  and a controlled two-reference Byte Voice v1 stress-test command.
- Optional `display_text`/`speech_text` fields for future pronunciation normalization without
  changing current captions.
- Optional ElevenLabs narration provider using the official Python SDK, configurable voice
  identity/version, safe request metadata, and bounded transient retries.
- Offline mocked tests for ElevenLabs configuration, SDK boundary behavior, and TTS fingerprints.
- Structured five-scene script roles for hook, context, fact, development, and conclusion.
- `CaptionAlignmentProvider` with deterministic fake known-text word timings and an isolated
  optional WhisperX adapter path.
- `caption_alignment` artifacts, ASS dynamic caption generation, caption grouping, and
  active-word emphasis.
- Reusable Byte presenter character definition and transparent PNG pose assets.
- Presenter scene instructions, local character asset loading, pose validation, and
  character-version/content fingerprints.
- `resolve_presenters` pipeline step with a `presenters.json` reference artifact.
- FFmpeg presenter overlay composition with subtitle-safe placement and fade-in/fade-out.
- Offline tests for character loading, deterministic presenter planning, renderer inputs, and
  the integrated review-ready vertical slice.

### Changed

- Byte's selected voice is now versioned as `byte_voice_v1`; local CLI settings default to
  `TTS_MODE=cached` so visual development cannot trigger paid narration accidentally.
- Manual TTS provider selection now supports `elevenlabs`; SFX and music remain deferred.
- The deterministic manual script now places Byte in two scenes with different poses while
  leaving presenter data optional for other scenes.
- Manual run configuration includes `DEFAULT_CHARACTER_ID`.
- The reusable character presenter slice has now been validated with a live Edge TTS + Pexels
  manual run after explicit `.env` authorization.
- Byte now appears in every generated scene by default, and final render reuse fingerprints
  include captions, alignment, presenter references, visual assets, and narration inputs.

## 2026-09-05

### Added

- Replaceable Edge/fake TTS and Pexels/fake asset adapters, with ffprobe-backed audio
  inspection and a narration-driven three-scene timeline.
- Topic, language, optional target duration, and provider configuration for manual runs.
- Per-scene visual queries, Pexels provenance and attribution metadata, portrait-first media
  selection, and deterministic local fallback when a query has no result.
- Dedicated audio, timeline, background, and subtitle StepRuns with persisted input
  fingerprints and a JSON timeline artifact.
- End-to-end checks for dynamic duration, synchronized subtitles, stable artifact IDs,
  H.264/AAC output, and final review state.
- Automatic `vertical-slice-implementer` skill for turning authorized product changes into
  minimal executable slices before architecture review, QA, and documentation.
- Automatic `architecture-guardian` skill enforcing dependency direction, cohesive ownership,
  small provider ports, and thin API/ORM/CLI adapters before QA.
- Automatic `code-quality-gate` skill covering uv reproducibility, Ruff, pytest, Git
  whitespace, artifact hygiene, and conditional FFmpeg validation.
- Executable deterministic CLI flow from fixture candidate to human review queue.
- Local PPM scene assets, reproducible WAV audio, SRT subtitles, FFmpeg rendering, and
  `ffprobe` validation.
- Idempotency key, durable step records, artifact hashes, and separation of work/final files.
- Review queue, production detail, local artifact serving, and approve/reject/change-request
  API operations.
- End-to-end integration coverage for rendering, validation, idempotency, persistence, and
  human review.
- Modular MVP foundation with separate API, worker, and scheduler process boundaries.
- Domain states, Pydantic contracts, SQLAlchemy persistence models, and safe local artifact
  paths.
- Deterministic fixture and editorial providers for the first vertical slice.
- Unit and integration test skeleton covering contracts, architecture, persistence, and API.
- Project-level `feature-documenter` skill with automatic documentation at the end of every
  meaningful development change.
- Reproducible dependency lock in `uv.lock`.

### Changed

- Ignored `.test-temp/` so local test/runtime scratch files stay out of publication workflows.
- Replaced the fixed 30-second media timeline with word-weighted scenes fitted to observed
  narration duration, and strengthened validation with video codec, audio codec, and duration
  checks.
- Extended idempotency fingerprints to cover user input, provider configuration, narration,
  and asset queries; matching reruns reuse StepRuns, assets, and the final render.
- Extended the automatic development workflow to begin with repository-aware vertical-slice
  implementation while retaining separate authorization for Git publication.
- Decoupled pipeline orchestration and human review from SQLAlchemy, FastAPI, FFmpeg,
  subtitle, and local-storage implementations through project-owned ports and repositories.
- Moved state persistence to SQLAlchemy adapters, review transitions to an application
  service, and concrete wiring to the bootstrap composition root.
- Expanded architecture tests to enforce the pipeline dependency boundary.
- Ordered structural delivery as architecture guardian, quality gate, feature documentation,
  then explicitly authorized Git publication.
- Ordered the development handoff as quality gate first and feature documentation second;
  failed gates now block commit, push, and pull-request workflows.
- Advanced the deterministic production state through all steps to `awaiting_review`.
- Standardized Python environment and dependency management on `uv`.
- Established zero mandatory operating cost and replaceable providers as MVP constraints.
- Verified all 17 tests on Python 3.12.14; recorded two non-blocking upstream deprecation
  warnings and two pending Ruff import-order findings.
