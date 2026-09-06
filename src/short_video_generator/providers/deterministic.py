from collections.abc import Sequence

from short_video_generator.contracts import (
    CandidateInput,
    EditorialBrief,
    ScriptScene,
    VideoScript,
)


class FixtureSourceProvider:
    """In-memory source used by tests and local vertical slices."""

    def __init__(self, candidates: Sequence[CandidateInput]) -> None:
        self._candidates = tuple(candidates)

    def fetch(self, niche: str) -> list[CandidateInput]:
        del niche
        return list(self._candidates)


class DeterministicEditorialProvider:
    """Simple three-scene strategy; it does not call a model or external service."""

    def __init__(self, language: str = "en", target_duration_seconds: int | None = None) -> None:
        self.language = language
        self.target_duration_seconds = target_duration_seconds or 30

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
        if self.language.lower().startswith("es"):
            narrations = (
                f"Esta es una explicación breve de {brief.topic}.",
                brief.key_points[0],
                f"Esa es la idea principal detrás de {brief.topic}.",
            )
        else:
            narrations = (
                f"Here is a quick explanation of {brief.topic}.",
                brief.key_points[0],
                f"That is the core idea behind {brief.topic}.",
            )
        visual_queries = (
            f"{brief.topic} technology concept",
            f"{brief.topic} developer workflow",
            f"{brief.topic} practical benefits",
        )
        return VideoScript(
            title=brief.topic,
            hook=brief.promise,
            scenes=tuple(
                ScriptScene(
                    order=index,
                    narration=narration,
                    on_screen_text=(brief.topic if index == 1 else narration[:120]),
                    visual_direction="Full-frame visual asset with readable caption",
                    visual_query=visual_queries[index - 1],
                    duration_seconds=10,
                )
                for index, narration in enumerate(narrations, start=1)
            ),
            closing=narrations[-1],
        )
