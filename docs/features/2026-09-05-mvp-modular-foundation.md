# MVP modular foundation

- **Date:** 2026-09-05
- **Status:** Completed with runtime verification pending
- **Branch:** `feat/mvp-modular-foundation`

## Objective

Establish the first reviewable foundation for a local modular monolith that generates
vertical videos and always ends in human review. Keep API, worker, scheduler, domain,
pipeline, providers, persistence, and rendering independently replaceable.

## Delivered behavior

- Created separate entry points for the FastAPI process, worker, and scheduler.
- Added a health endpoint while leaving operational API endpoints deferred.
- Defined production and review states with guarded transitions.
- Added a fixture source and deterministic editorial provider for repeatable tests.
- Defined the minimal vertical template as 1080 x 1920 at 30 fps.
- Kept generated assets outside SQLite and restricted artifact contracts to safe relative
  paths.

The worker and scheduler currently expose process boundaries only. They do not yet claim or
execute jobs.

## Architecture and contracts

- Pure domain rules live under `src/short_video_generator/domain/` and do not import web,
  persistence, validation, or process-execution frameworks.
- Provider protocols for sources, editorial generation, TTS, media, and rendering live in
  `src/short_video_generator/providers/ports.py`.
- Versioned Pydantic contracts cover configuration, candidates, evaluation, editorial
  briefs, scripts, assets, rendering, validation, and human review.
- SQLAlchemy models cover niches, source configuration, pipeline and step runs, topic
  candidates, productions, artifacts, and reviews.
- SQLite stores state and artifact metadata; local directories store binary assets and
  renders.

## Product constraints

- The default vertical slice must have zero mandatory operating cost.
- Local and deterministic providers are the default path.
- Paid or remote providers may only be optional, replaceable adapters.
- Publication, authentication, Redis, Celery, microservices, and multiple platforms remain
  outside this phase.
- Python environments and dependencies are managed with `uv`.
- Feature documentation is triggered automatically before handing off any meaningful
  development change; it does not require a user reminder.

## Validation

- Added unit tests for contracts, state transitions, provider determinism, safe artifact
  paths, and architecture boundaries.
- Added integration tests for SQLite schema creation and the API health endpoint.
- `git diff --check` completed without whitespace errors.
- The Python test suite was not executed because Python and `uv` are not available in the
  current environment. FFmpeg is also unavailable.

## Deferred work

- Pipeline orchestration and durable job claiming.
- Scheduler run creation.
- Review queue endpoints and UI.
- Local TTS and media adapters.
- FFmpeg rendering and `ffprobe` validation.
- Runtime execution of the existing tests and generation of `uv.lock`.
