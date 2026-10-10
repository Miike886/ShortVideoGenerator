# Editorial Gate

## Status

Implemented as an application step on 2026-09-06.

## Pipeline boundary

The manual production flow now follows:

`Story -> EditorialGate -> TTS cache -> ElevenLabs if needed -> Visuals -> Render`.

The gate runs after script creation and before narration generation. A passing plan records
the gate version and fingerprint in its `StepRun` and allows media production to continue.
A rejected plan marks the production as `failed`, records the failed step and stops before
the TTS provider is called.

## Validation rules

The gate requires a `SemanticStoryPlan`, contiguous scenes beginning with a hook, at least
one explanatory or concrete role, a resolving final role, non-duplicate `new_information`,
and a nonempty visual subject for every scene. Duplicate detection uses normalized exact
matches; abstract visuals are rejected when explicitly labeled as abstract. These are
structural checks, not a semantic assessment of the narration or visuals.
Diagnostics remain deterministic and local;
the gate does not use research, embeddings, LLMs or provider calls.

## Fingerprints and tests

The gate fingerprint includes the gate version, story plan and renderable script. Changes to
the semantic story therefore invalidate the appropriate downstream work without coupling
the gate to ElevenLabs internals. Tests cover both the passing path and the stop condition,
including the guarantee that a rejected story leaves TTS invocation count at zero.

## Limits and publication validation (2026-10-10)

Already-completed production reuse returns before this gate; standalone TTS reference
commands are outside the production gate. The gate does not guarantee factual accuracy,
explanatory depth, or that a final role actually resolves the opening claim.

The full suite passed: 56 tests, including rejection-before-TTS and passing-flow coverage.
Architecture checks, Ruff, lockfile validation and Git whitespace checks passed. Two
upstream test-client deprecation warnings remain.
