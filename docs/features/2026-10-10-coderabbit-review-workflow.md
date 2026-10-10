# CodeRabbit advisory review workflow

## Status and scope

Repository configuration and pre-PR instructions implemented on 2026-10-10. No product
code, runtime dependencies, CI workflows or GitHub branch protections changed.
CodeRabbit installation, repository access and a successful remote review must be verified
separately; adding YAML alone does not install the GitHub App.

## Delivered behavior

- Root `.coderabbit.yaml` requests Spanish, balanced reviews, automatic reviews of
  non-draft PRs and incremental review after pushes.
- Automatic approval is disabled; author-triggered approval is also disabled.
- Path instructions prioritize architecture, feature integrity, state transitions,
  fingerprints, narration reuse, paid-request safety, offline tests and accurate docs.
- `AGENTS.md` requires risk-appropriate tests, local gates, documentation and a mini
  review of the complete branch diff before publishing a PR. Blocking local findings must
  be fixed before publication.
- CodeRabbit supplements local checks. Its findings must be assessed rather than applied
  blindly, and valid fixes require tests and renewed QA. Merge still requires user approval.

## Validation

- Parsed YAML with PyYAML and validated it with jsonschema against the official
  `https://coderabbit.ai/integrations/schema.v2.json` schema. Validation dependencies were
  temporary `uv run --with` dependencies, not additions to the project or lockfile.
- `uv lock --check` and `uv run ruff check .` passed.
- `uv run pytest`: 56 passed, including FFmpeg integration and architecture boundaries.
  Two existing upstream test-client deprecation warnings remain.
- Configuration-only scope requires schema validation, not new artificial product tests.
- Local mini-review found no blocking issues; integration availability remains unverified.

## Remote trial

Install or enable the CodeRabbit GitHub App for this repository, open a non-draft PR and
verify a response from `coderabbitai[bot]` for the latest commit. If necessary, request a
review with `@coderabbitai review`. Inspect the configuration source reported by the bot;
do not assume this initial PR uses its new YAML before it is merged into the base branch.
Keep the trial PR open until the remote review has been assessed. No automatic merge or
required remote checks are introduced by this slice.

## References

- [CodeRabbit setup](https://docs.coderabbit.ai/getting-started/quickstart)
- [Configuration reference](https://docs.coderabbit.ai/reference/configuration)
