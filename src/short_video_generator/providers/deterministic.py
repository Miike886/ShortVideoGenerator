from collections.abc import Sequence

from short_video_generator.contracts import (
    CandidateInput,
    EditorialBrief,
    PresenterInstruction,
    ScriptScene,
    VideoScript,
)
from short_video_generator.pipeline.story import DeterministicStoryPlanner


class FixtureSourceProvider:
    """In-memory source used by tests and local vertical slices."""

    def __init__(self, candidates: Sequence[CandidateInput]) -> None:
        self._candidates = tuple(candidates)

    def fetch(self, niche: str) -> list[CandidateInput]:
        del niche
        return list(self._candidates)


class DeterministicEditorialProvider:
    """Structured short strategy; it does not call a model or external service."""

    def __init__(
        self,
        language: str = "en",
        target_duration_seconds: int | None = None,
        character_id: str = "byte",
    ) -> None:
        self.language = language
        self.target_duration_seconds = target_duration_seconds or 30
        self.character_id = character_id

    def create_brief(self, candidate: CandidateInput) -> EditorialBrief:
        return EditorialBrief(
            topic=candidate.title,
            angle=f"Explain briefly: {candidate.title}",
            audience="General audience",
            promise=f"Understand {candidate.title} in a short explanation",
            key_points=(candidate.summary,),
            tone="clear",
            target_duration_seconds=self.target_duration_seconds,
            source_urls=(str(candidate.canonical_url),),
        )

    def create_script(self, brief: EditorialBrief) -> VideoScript:
        story = DeterministicStoryPlanner().create(brief)
        poses = ("explaining", "thinking", "surprised", "pointing_left", "happy")
        positions = (
            "bottom_right",
            "bottom_left",
            "bottom_right",
            "bottom_right",
            "bottom_left",
        )
        scene_duration = self.target_duration_seconds / len(story.scenes)
        return VideoScript(
            title=brief.topic,
            hook=brief.promise,
            scenes=tuple(
                ScriptScene(
                    order=scene.order,
                    narration=scene.narration,
                    on_screen_text=(brief.topic if scene.order == 1 else scene.narration[:120]),
                    visual_direction=(
                        f"{scene.visual_concept.subject}; "
                        f"{scene.visual_concept.observable_action}"
                    ),
                    visual_query="",
                    duration_seconds=scene_duration,
                    presenter=PresenterInstruction(
                        character_id=self.character_id,
                        pose=poses[scene.order - 1],
                        position=positions[scene.order - 1],
                        scale=0.32 if scene.order in {1, 3} else 0.3,
                    ),
                    role=scene.role,
                )
                for scene in story.scenes
            ),
            closing=story.scenes[-1].narration,
            story_plan=story,
        )
