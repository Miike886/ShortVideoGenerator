# Semantic story planning

## Status

Implemented as a deterministic, offline story-planning slice on 2026-09-06.

## Delivered behavior

- `SemanticStoryPlan` stores a central claim and an ordered set of semantic scene plans.
- Each scene records a communicative goal, new information, relation to the previous scene,
  viewer knowledge delta, narration, and a concrete `VisualConcept`.
- The deterministic editorial provider now derives renderable scenes from the story plan,
  using a fixed five-stage baseline: hook, context, mechanism, example and payoff.
  Adaptive scene counts are not implemented.
- Visual concepts describe recordable subjects and observable actions separately from stock
  search queries. The visual planner turns those concepts into search plans with
  alternatives and avoid terms.
- Story plans expose deterministic redundancy diagnostics and a readable `debug_text()`
  representation. Duplicate new information and direct central-claim restatements are
  flagged without embeddings or external services.
- Semantic story data is serialized inside the existing `VideoScript`, so production
  persistence and downstream fingerprints continue using the existing architecture.

## Boundaries and fingerprints

The story layer depends on project contracts and deterministic application planning only;
it has no FFmpeg, Pexels, database or external model dependency. A semantic plan is part of
the script fingerprint, so changes that alter narration invalidate TTS and alignment. A
visual-concept-only change remains downstream of the script and can invalidate visual
planning/rendering without changing the TTS provider fingerprint.

## Limitations

The current planner is intentionally a structural baseline. It does not perform research,
fact verification, citations, topic selection, editorial persona, embeddings or LLM-based
rewriting. Generic narration and visual concepts still require topic-aware refinement;
structural checks do not guarantee explanatory depth or literal visual relevance.
CTA, evidence and contrast roles are supported by the
contract vocabulary but are not forced into every deterministic script.

## Publication validation (2026-10-10)

The complete suite passed with 56 tests, including FFmpeg integration and architecture
boundary checks. Ruff, the lockfile check and Git whitespace checks passed. Two upstream
test-client deprecation warnings remain. A local preview was re-rendered with cached real
ElevenLabs narration, Pexels clips and Byte assets; ffprobe validated H.264/AAC portrait
output at 34.966667 seconds. This preview was not a new full production execution.
