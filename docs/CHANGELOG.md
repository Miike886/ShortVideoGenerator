# Development changelog

This changelog records meaningful product and architecture changes. Detailed context lives
in the linked records under `docs/features/`.

## 2026-09-05

### Added

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
