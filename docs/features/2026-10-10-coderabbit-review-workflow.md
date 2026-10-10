# CodeRabbit advisory review workflow

## Status and scope

Repository configuration and pre-PR instructions implemented on 2026-10-10. No product
code, runtime dependencies, CI workflows or GitHub branch protections changed.
The GitHub integration and a completed manual review were verified on PR #8 for commit
`b8f7b7b`. Adding YAML alone does not install the GitHub App. Follow-up commits still
require review; the initial review is not approval of later changes.

## Delivered behavior

- Root `.coderabbit.yaml` requests Spanish, balanced reviews, automatic reviews of
  non-draft PRs and incremental review after pushes, with automatic commit-count pausing
  disabled. Account-level eligibility and usage limits can still prevent a review.
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
- Local mini-review found no blocking issues. Follow-up schema validation also checks
  `auto_pause_after_reviewed_commits == 0`; the full 56-test suite and local gates passed
  again after the review fixes.

## Remote trial

CodeRabbit recognized the repository YAML and completed a manually triggered review in
about five minutes. It posted two minor findings: disable the default pause after five
reviewed commits, and describe tests as risk-appropriate in the changelog. Both findings
were verified locally and corrected.

The bot initially skipped automatic review because the repository had fewer than ten
stars. Its completed review also reported one included review per hour and no remaining
included reviews for that hour. Disabling commit-count pausing does not remove these
service-side limits. No additional manual review was requested for the follow-up commit.

Install or enable the CodeRabbit GitHub App for this repository, open a non-draft PR and
verify a response from `coderabbitai[bot]` for the latest commit. If necessary, request a
review with `@coderabbitai review`. Inspect the configuration source reported by the bot;
do not assume this initial PR uses its new YAML before it is merged into the base branch.
Keep the trial PR open until the remote review has been assessed. No automatic merge or
required remote checks are introduced by this slice.

## References

- [CodeRabbit setup](https://docs.coderabbit.ai/getting-started/quickstart)
- [Configuration reference](https://docs.coderabbit.ai/reference/configuration)
