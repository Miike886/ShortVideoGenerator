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
