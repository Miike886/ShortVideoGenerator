# Automatic architecture guardian

- **Date:** 2026-09-05
- **Status:** Completed; vertical slice cleared with a maintainability note
- **Branch:** `feat/deterministic-vertical-slice`

## Objective

Automatically preserve module ownership and dependency direction after structural changes,
before the code quality gate and any publication workflow.

## Delivered workflow

- Added the project-local `architecture-guardian` skill with automatic triggering for module,
  interface, model, dependency, ownership, and responsibility changes.
- Defined inward dependency rules for domain, contracts, pipeline, ports, adapters,
  persistence, API, CLI, and composition roots.
- Defined evidence-based reviews for cohesion, naming, duplication, dead code, and provider
  interface size without imposing subjective abstractions.
- Limited automatic corrections to small, unambiguous, in-scope changes.
- Required explicit authorization for broad refactors.
- Classified reviews as `clear`, `clear-with-notes`, or `blocked`; blocked reviews prevent QA,
  commit, push, and pull request.
- Updated `AGENTS.md` to enforce architecture guardian, quality gate, and feature documenter
  in that order.

## Validation performed

The `skill-creator` validator reported `Skill is valid!`. A targeted review inspected imports,
module sizes, business transitions, ORM operations, and the existing architecture tests.

## Authorized refactor applied

- Added project-owned execution repository, artifact store, subtitle, validation, and review
  repository ports under `pipeline/`.
- Replaced ORM-backed pipeline state with framework-independent execution, candidate,
  production, step, artifact, and review models.
- Moved SQLAlchemy mapping and persistence into `persistence/repositories.py`.
- Extracted step lifecycle persistence into `pipeline/steps.py` and human-review transitions
  into `pipeline/review.py`.
- Reduced `api/app.py` to HTTP translation and delegated review rules to `ReviewService`.
- Centralized concrete adapter wiring in `bootstrap.py`.
- Extended architecture tests to reject FastAPI, SQLAlchemy, subprocess, persistence, local
  storage, rendering, or deterministic-provider imports from `pipeline`.

## Final architecture result

`clear-with-notes`: dependency direction and business-rule ownership are clear. The manual
pipeline coordinator remains a sizeable file because it expresses the complete ordered use
case; this is a non-blocking extraction signal if later slices add branching or retries, not
a reason to introduce more abstractions in the current MVP.

The architecture gate allows the code quality gate and publication workflow.
