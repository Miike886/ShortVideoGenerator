# Automatic vertical slice implementer

- **Date:** 2026-09-05
- **Status:** Completed
- **Branch:** `feat/deterministic-vertical-slice`

## Objective

Make implementation requests follow a consistent repository-specific path from an approved
requirement to the smallest executable and testable product slice, without requiring the
user to invoke the workflow manually.

## Delivered workflow

- Added the project-local `vertical-slice-implementer` skill with automatic discovery for
  requests to implement, build, add, or materially change product behavior.
- Requires repository inspection followed by a brief plan and explicit validation commands
  before editing.
- Keeps implementation constrained to the requested acceptance criteria and records
  deliberately deferred work.
- Requires focused tests and a meaningful integration path proportional to the feature.
- Preserves the modular-monolith boundaries, `uv` dependency workflow, local file storage,
  and deterministic, replaceable, zero-mandatory-cost default providers.
- Hands completed structural work to `architecture-guardian`, `code-quality-gate`, and
  `feature-documenter` in that order.

## Trigger and authority boundaries

The skill skips planning-only, read-only, documentation-only, skill-maintenance, and trivial
formatting tasks. It cannot expand feature scope, introduce deferred platform capabilities,
authorize broad refactors, call external providers, or perform commits, pushes, pull
requests, merges, releases, or deployments without separate user authorization.

## Validation performed

The `skill-creator` validator reported `Skill is valid!`. `git diff --check` found no
whitespace errors; Git reported only the expected Windows line-ending notices.

Application tests were not run because this change affects development instructions and
documentation only, not runtime code, dependencies, schemas, or product behavior.
