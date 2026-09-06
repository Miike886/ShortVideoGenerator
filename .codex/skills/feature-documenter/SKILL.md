---
name: feature-documenter
description: Automatically document every completed development phase or meaningful implementation, fix, refactor, architecture, configuration, dependency, schema, test, or behavior change in this repository. Always use before handing off such work; do not wait for the user to request documentation. Skip read-only analysis and trivial formatting-only edits.
---

# Feature Documenter

Keep the repository's implementation history accurate, navigable, and useful to a future
maintainer.

## Automatic trigger

Invoke this skill automatically before the final handoff whenever the current task changed
code, tests, dependencies, configuration, architecture, schemas, runtime behavior, or a
development workflow. The user does not need to mention documentation or this skill.

Do not trigger it for read-only inspection, questions, planning with no repository changes,
or purely cosmetic edits that have no maintenance value. If a task contains several related
edits, document them once as a cohesive phase after implementation and verification.

## Documentation locations

- Store one record per development phase or cohesive feature in `docs/features/`.
- Maintain the chronological index in `docs/features/README.md`.
- Maintain the concise cross-feature change record in `docs/CHANGELOG.md`.

Use `YYYY-MM-DD-short-slug.md` for a new record. If the same phase already has a record,
update it instead of creating a duplicate.

## Workflow

1. Inspect the actual diff, relevant source files, contracts, migrations, and test results.
2. Separate implemented behavior from plans or deferred work. Never present an unexecuted
   test, unavailable dependency, or intended feature as completed.
3. Create or update the phase record with only the sections that carry useful information:
   - status and objective;
   - delivered behavior;
   - architecture, contracts, or data changes;
   - important files;
   - validation performed and its result;
   - decisions and constraints;
   - deferred work or known limitations.
4. Add or update its entry in `docs/features/README.md` using a repository-relative link.
5. Add concise `Added`, `Changed`, `Fixed`, or `Removed` entries to the current date in
   `docs/CHANGELOG.md`. Avoid duplicating implementation detail from the phase record.
6. Check links, dates, status, and terminology against the repository before finishing.

## Documentation rules

- Write for maintainers: explain outcomes and boundaries, not a transcript of commands.
- Cite file paths and observable test evidence when they help verification.
- Preserve previous history. Correct inaccurate entries explicitly rather than silently
  rewriting the meaning of an older phase.
- Keep secrets, credentials, personal data, raw provider payloads, and generated binaries
  out of documentation.
- Record paid or remote providers as optional when the local free path remains the default.
- Documentation changes belong to the same branch/change set as the implementation they
  describe, but this skill does not authorize commits, pushes, pull requests, or releases.
