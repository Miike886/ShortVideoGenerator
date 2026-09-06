# Development changelog

This changelog records meaningful product and architecture changes. Detailed context lives
in the linked records under `docs/features/`.

## 2026-09-05

### Added

- Modular MVP foundation with separate API, worker, and scheduler process boundaries.
- Domain states, Pydantic contracts, SQLAlchemy persistence models, and safe local artifact
  paths.
- Deterministic fixture and editorial providers for the first vertical slice.
- Unit and integration test skeleton covering contracts, architecture, persistence, and API.
- Project-level `feature-documenter` skill with automatic documentation at the end of every
  meaningful development change.

### Changed

- Standardized Python environment and dependency management on `uv`.
- Established zero mandatory operating cost and replaceable providers as MVP constraints.
