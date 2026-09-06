# Interactive visual storytelling

## Status

Implemented as an offline, deterministic vertical slice on 2026-09-06.

## Delivered behavior

- Each scene now produces a `SceneVisualDirection` with a bounded visual purpose,
  semantic subject, focal region, media preference, motion intent, Byte action/facing,
  entrance and normalized Byte beats.
- The workflow persists `visual-plan.json` as a `visual_plan` artifact and includes the
  selected subject, purpose, focal region and query in visual asset metadata.
- Byte choreography maps semantic actions to the validated local pose library, including
  left/right presentation, thinking, surprise, work and conclusion fallbacks. Placement is
  limited to the existing lower safe regions so captions remain unobstructed.
- FFmpeg resolves visual motion into deterministic reframing and resolves Byte slide/fade
  entrances while preserving the narration-driven scene durations.
- Pexels video candidates are scored for orientation and resolution before selection; the
  reusable ranking helper applies duration, media preference, quality and duplicate penalties.

## Architecture

`contracts.visuals` owns semantic data. `pipeline.visuals` owns deterministic planning,
choreography mapping and candidate ranking. Pexels and FFmpeg remain infrastructure
adapters. The existing `Production`/`StepRun`/`Artifact` state remains the persistence
boundary; no parallel visual database was added.

Visual planning is fingerprinted independently from TTS. The planner, choreography and
asset-selection versions are explicit so visual heuristic changes do not silently reuse an
old render, while narration artifacts remain reusable.

## Known limitations and deferred work

The current planner uses deterministic scene roles and text heuristics rather than semantic
embeddings or an LLM. Pexels metadata cannot establish true semantic relevance, and the
provider still falls back to the existing fake asset when no result is available. Byte
beats currently describe pose changes and are persisted for inspection; richer mid-scene
pose switching and object-aware focal detection remain future work. New Byte artwork,
generative visuals, SFX, music and editorial/content changes are out of scope.
