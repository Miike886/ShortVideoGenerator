# Automatic code quality gate

- **Date:** 2026-09-05
- **Status:** Completed
- **Branch:** `feat/deterministic-vertical-slice`

## Objective

Make QA an automatic development responsibility after implementation and before any commit,
push, or pull request, without requiring a user reminder.

## Delivered workflow

- Added the project-local `code-quality-gate` skill with automatic discovery instructions.
- Updated `AGENTS.md` so the gate runs before feature documentation and publication.
- Defined reproducibility checks for `uv.lock` and the synchronized development environment.
- Defined mandatory Ruff, applicable pytest, `git diff --check`, and artifact hygiene checks.
- Added conditional FFmpeg, `ffprobe`, codec, filter, integration, and output-contract checks
  when rendering-related code changes.
- Classified results as `passed`, `passed-with-warnings`, or `failed` using explicit rules.
- Made a failed gate block commit/push/PR while preserving separate authorization for every
  external Git action.

The skill reports exact skipped checks, warnings, and blockers. It does not delete user files,
fabricate outcomes, upgrade dependencies, or authorize publication.

## Validation performed

- The `skill-creator` validator reported `Skill is valid!`.
- `uv lock --check` resolved the locked graph successfully.
- `uv sync --locked --dev` checked all project packages successfully.
- `uv run ruff check .` passed.
- The full suite passed 25 tests, including the FFmpeg end-to-end integration.
- FFmpeg exposed H.264/AAC encoders and scale, drawtext, and subtitles filters.
- `ffprobe` confirmed the observed render is H.264, 1080 x 1920, 30 fps, and 30 seconds.
- No `.partial` files or unexpected tracked runtime artifacts were found.

## Gate result

`passed-with-warnings`: two non-blocking upstream deprecation warnings remain in the
Starlette/AnyIO test stack. There are no QA blockers.
