---
name: architecture-guardian
description: Automatically review repository architecture whenever implementation changes modules, interfaces, models, dependencies, ownership, or responsibilities. Enforce dependency direction, framework isolation, cohesive modules, small provider ports, and thin API/ORM/CLI adapters before QA. Skip documentation-only and trivial local fixes.
---

# Architecture Guardian

Protect the modular monolith's boundaries without optimizing for a subjective ideal. Invoke
this skill automatically after structural implementation and before `code-quality-gate`.
The user does not need to request an architecture review.

## Intended dependency direction

- `domain` contains business states and rules and depends only on the standard library.
- `contracts` may depend on `domain` and Pydantic, but not on FastAPI, SQLAlchemy, FFmpeg, or
  concrete providers.
- `pipeline` coordinates use cases through domain types, contracts, provider ports, and
  repository/storage ports. It must not import FastAPI, SQLAlchemy, ORM records, subprocess,
  or concrete adapters.
- Provider ports remain small and capability-focused. Concrete provider and rendering
  adapters may depend on their ports and project contracts, never the reverse.
- Persistence implements repository ports with SQLAlchemy. ORM records contain mappings and
  relationship configuration, not workflow or editorial rules.
- API routers, CLI commands, worker, and scheduler translate inputs and call use cases. They
  do not own scoring, selection, state transitions, artifact policy, or rendering decisions.
- Bootstrap/composition code is the only place that wires concrete adapters to use cases.

These boundaries should keep an eventual process or service extraction possible without
rewriting the domain or pipeline.

## Review workflow

1. Inspect the actual diff and identify changed responsibilities, imports, public contracts,
   and data ownership. Preserve unrelated user work.
2. Trace dependency direction from each changed module. Use targeted searches or import
   tests rather than assumptions.
3. Check that business decisions live in domain/application policies and that infrastructure
   details remain in adapters.
4. Review provider interfaces for single capability, minimal parameters, project-owned
   return contracts, and absence of ORM/framework leakage.
5. Inspect cohesion and size. A long file is a signal, not an automatic violation; report it
   when it contains independent reasons to change, mixes layers, or makes testing require
   unrelated infrastructure.
6. Review naming, duplicated policies, dead paths, and unclear ownership. Cite concrete
   symbols and consumers; do not recommend abstractions without an observed duplication or
   boundary need.
7. Correct only small, unambiguous, in-scope issues when implementation edits remain
   authorized, such as a misplaced import, a clearly wrong name, or a trivial extraction.
8. For broad refactors, stop and report a concrete migration proposal: current coupling,
   target port/module, affected consumers, sequencing, and test protection. Do not perform
   the refactor without user authorization.

## Severity and blocking

- `clear`: no material architecture findings.
- `clear-with-notes`: only non-blocking maintainability observations remain.
- `blocked`: dependency inversion, framework or ORM leakage into `domain`/`pipeline`, business
  logic in API/ORM/CLI, a cyclic dependency, a provider-specific contract leaking inward, or
  another finding that would make the next feature materially harder to change or extract.

A `blocked` result prevents moving to QA, commit, push, or PR. Small fixes must be reviewed
again after correction. Broad refactors require explicit user direction.

This skill does not authorize commits, pushes, pull requests, merges, releases, destructive
cleanup, dependency upgrades, or scope expansion.

## Handoff report

Return a compact, evidence-based report:

```text
Architecture guardian: clear | clear-with-notes | blocked
Findings:
- [severity] <module:symbol> — <observed coupling and impact>
Safe fixes applied:
- <fix or none>
Proposed refactors:
- <proposal or none>
Next gate:
- code-quality-gate allowed | blocked
```
