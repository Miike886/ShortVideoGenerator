---
name: code-quality-gate
description: Automatically validate this repository after implementation and before any commit, push, or pull request. Run Ruff, applicable tests, lockfile and dependency checks, Git whitespace and artifact checks, and FFmpeg validation when rendering changed; report passed, passed-with-warnings, or failed. Do not publish when the gate fails. Skip read-only and documentation-only tasks unless explicitly requested.
---

# Code Quality Gate

Provide a reproducible quality decision from observed command results. Invoke this skill
automatically after implementation and immediately before a requested commit, push, or pull
request. The user does not need to request QA separately.

## Gate workflow

1. Inspect `git status --short`, the relevant diff, and the files changed from the intended
   base. Do not include unrelated user changes in fixes or conclusions.
2. Verify dependency reproducibility:
   - run `uv lock --check`;
   - run `uv sync --locked --dev` when the environment needs synchronization;
   - fail if `pyproject.toml` and `uv.lock` disagree or a required dependency cannot be
     installed.
3. Run `uv run ruff check .`.
4. Run tests proportionally during iteration, then run the complete `uv run pytest` before a
   commit or PR. A relevant integration test that is skipped does not count as passing.
5. Run `git diff --check`.
6. Inspect `git status --short` and the runtime directories for tracked or unexpected
   temporary outputs, `.partial` files, databases, renders, credentials, or caches. Do not
   delete user files automatically; report exact paths and clean only files created by the
   current task when safe.
7. When rendering, audio, subtitles, media validation, or their configuration changed:
   - verify `ffmpeg` and `ffprobe` from `PATH` or the configured explicit paths;
   - verify the required codecs and filters when relevant;
   - run the end-to-end rendering integration test;
   - inspect the produced file with `ffprobe` and compare its observed properties with the
     requested contract.
8. If an in-scope failure has a small, unambiguous fix and implementation changes are still
   authorized, fix it and rerun every affected check. Otherwise stop with `failed`.

Never fabricate a result, treat a skipped required check as passed, or claim that a warning
is harmless without identifying its source and impact.

## Decision rules

- `passed`: every required check ran and passed; no material warnings or unwanted artifacts
  remain.
- `passed-with-warnings`: every required check ran and passed, and only identified,
  non-blocking warnings remain.
- `failed`: any required command failed; a relevant test was skipped; the lockfile is stale;
  a required tool is unavailable; unexpected tracked/runtime artifacts remain; or the
  rendered output violates its contract.

This skill does not authorize commits, pushes, pull requests, merges, releases, dependency
upgrades, destructive cleanup, or unrelated refactors. A passing gate only removes the QA
blocker; the underlying external action still requires user authorization.

## Handoff report

Return a brief report in this shape:

```text
Quality gate: passed | passed-with-warnings | failed
Checks:
- <check>: <observed result>
Warnings:
- <warning or none>
Blockers:
- <blocker or none>
```

Include exact failing commands or paths only when they help the next action. If the result is
`failed`, explicitly state that commit/push/PR is blocked.
