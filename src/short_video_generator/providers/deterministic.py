from collections.abc import Sequence

from short_video_generator.contracts import (
    CandidateInput,
    EditorialBrief,
    PresenterInstruction,
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
        if self.language.lower().startswith("es"):
            narrations = (
                f"{brief.topic} no es solo una idea llamativa.",
                f"En la practica, {brief.topic} importa porque cambia como se entiende "
                "el problema.",
                brief.key_points[0],
                "La parte util aparece cuando esa explicacion se conecta con una "
                "decision concreta.",
                f"Por eso {brief.topic} funciona mejor como una historia clara que como "
                "una lista de ganchos.",
            )
        else:
            narrations = (
                f"{brief.topic} is not just a catchy idea.",
                f"In practice, {brief.topic} matters because it changes how the problem "
                "is understood.",
                brief.key_points[0],
                "The useful part appears when that explanation connects to a concrete decision.",
                f"That is why {brief.topic} works better as a clear story than as a list of hooks.",
            )
        visual_queries = (
            f"{brief.topic} social media hook",
            f"{brief.topic} context explanation",
            f"{brief.topic} factual detail",
            f"{brief.topic} practical decision",
            f"{brief.topic} clear conclusion",
        )
        roles = ("hook", "context", "fact", "development", "conclusion")
        poses = ("explaining", "thinking", "surprised", "pointing_left", "happy")
        positions = (
            "bottom_right",
            "bottom_left",
            "bottom_right",
            "bottom_right",
            "bottom_left",
        )
        scene_duration = self.target_duration_seconds / len(narrations)
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
                    duration_seconds=scene_duration,
                    presenter=PresenterInstruction(
                        character_id=self.character_id,
                        pose=poses[index - 1],
                        position=positions[index - 1],
                        scale=0.32 if index in {1, 3} else 0.3,
                    ),
                    role=roles[index - 1],
                )
                for index, narration in enumerate(narrations, start=1)
            ),
            closing=narrations[-1],
        )
