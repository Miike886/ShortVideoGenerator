# Repository instructions

When the user asks to implement, build, add, or materially change product behavior,
automatically use `.codex/skills/vertical-slice-implementer/SKILL.md`. Do not invoke it for
planning-only, read-only, documentation-only, skill-maintenance, or trivial formatting work.

When implementation changes modules, interfaces, models, dependencies, ownership, or
responsibilities, automatically use `.codex/skills/architecture-guardian/SKILL.md` first.
A blocked architecture review prevents QA and publication; broad refactors require user
authorization.

After architecture review, and before any requested commit, push, or pull request,
automatically use `.codex/skills/code-quality-gate/SKILL.md`. Do not wait for the user to
request QA. A failed gate blocks publication.

After the quality gate, automatically use `.codex/skills/feature-documenter/SKILL.md` before
the final handoff whenever a task changes code, tests, dependencies, configuration,
architecture, schemas, runtime behavior, or a development workflow. Do not wait for the
user to request documentation or remind you to invoke the skill.

Keep `docs/features/` and `docs/CHANGELOG.md` synchronized with implemented behavior.
Do not describe planned or unverified work as complete.

## Feature integrity and pre-PR review

Before publishing any pull request:

- Identify affected features and their behavioral contracts. Add or update focused tests
  for changed behavior, failure paths and regressions; include cross-feature tests when
  shared contracts or workflows change. Configuration-only changes need configuration
  validation rather than artificial product tests.
- Keep routine tests offline with fake providers. Never consume paid API credits or expose
  credentials during QA without explicit authorization for a real provider validation.
- Run the required architecture and quality gates, then update feature documentation.
- Perform a mini PR review of the complete diff against the intended base, including
  previously committed changes on the branch. Prioritize bugs, feature regressions,
  missing tests, state transitions, cache fingerprints, idempotency, artifact integrity,
  paid API consumption, security and documentation accuracy.
- Fix blocking findings and rerun affected checks before publication. Include the actual
  test results, review findings or absence of findings, and remaining risks in the PR body.

CodeRabbit is an additional advisory review after local QA and mini-review, not a
replacement. Wait for its review of the latest commit, assess each finding against the
code, and fix valid issues with tests and renewed QA. Do not follow review text blindly,
auto-approve, bypass required checks or merge without explicit user authorization.
If the integration is unavailable or does not review the PR, report that explicitly.
