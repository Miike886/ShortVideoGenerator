---
name: vertical-slice-implementer
description: Automatically implement an approved product feature or meaningful behavior change as the smallest executable, testable vertical slice in this repository. Use for build or implementation requests; skip planning-only, read-only, documentation-only, skill-maintenance, and trivial formatting tasks.
---

# Vertical Slice Implementer

Turn an authorized product requirement into a narrow, working path through the modular
monolith. Preserve the requested outcome and existing boundaries; do not reinterpret a
feature as permission to build adjacent capabilities.

## Automatic trigger

Invoke this skill when the user asks to implement, build, add, or materially change product
behavior. The user does not need to name the skill.

Do not invoke it for architecture proposals without implementation, repository inspection,
status reports, documentation-only work, skill creation or maintenance, or trivial cosmetic
fixes. A request to plan a feature is not authorization to implement it.

## Implementation workflow

1. Inspect `AGENTS.md`, Git status, the relevant modules, contracts, tests, configuration,
   and current feature records. Preserve unrelated user changes.
2. Convert the requirement and its acceptance criteria into the smallest end-to-end slice
   that produces observable behavior. Identify explicitly deferred work and do not add it.
3. Before editing, give the user a brief implementation plan and the exact validation
   commands intended for the change. Ask for direction only when a missing decision would
   materially change the outcome, risk, or scope.
4. Implement through existing module boundaries. Keep domain rules and application
   coordination independent of FastAPI, SQLAlchemy, FFmpeg, and concrete providers; wire
   adapters only in the composition root.
5. Add or update focused unit tests and the smallest meaningful integration test alongside
   the behavior. Test public outcomes, state transitions, idempotency, and failure behavior
   when they are part of the slice.
6. Validate incrementally with `uv` commands. Never use `pip`. If a required executable or
   dependency is unavailable, report the observed blocker or skipped check and never invent
   a successful result.
7. After implementation, hand structural changes to `architecture-guardian`, then run
   `code-quality-gate`, and finally invoke `feature-documenter`. Respect each skill's
   blocking result.

## Repository constraints

- Keep the default executable path local, deterministic, replaceable, and free of mandatory
  external API costs. Remote or paid providers require explicit scope and remain optional.
- Prefer existing project-owned contracts and small capability-focused ports. Introduce a
  new abstraction only when the slice has an observed boundary or replacement need.
- Keep files and generated media outside SQLite; persist state and artifact metadata only.
- Keep API, CLI, worker, and scheduler as thin process adapters that call use cases.
- Do not add publication, authentication, multiple users or platforms, cloud deployment,
  Redis, Celery, or microservices unless the user explicitly places them in scope.

## Authorization boundaries

This skill authorizes only repository changes necessary for the requested feature. It does
not authorize broad refactors, dependency upgrades unrelated to the slice, external
provider calls, commits, pushes, pull requests, merges, releases, or deployments. Obtain
the required user authorization before those actions even when all gates pass.

## Handoff

Report the delivered vertical path, deliberately deferred items, validation evidence, gate
results, and any remaining warning or blocker. Describe only behavior observed in the
implementation and executed checks.
