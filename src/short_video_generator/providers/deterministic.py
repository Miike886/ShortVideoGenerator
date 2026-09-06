from collections.abc import Sequence

from short_video_generator.contracts import (
    CandidateInput,
    EditorialBrief,
    ScriptScene,
    VideoScript,
)


class FixtureSourceProvider:
    """In-memory source used by tests and the first local vertical slice."""

    def __init__(self, candidates: Sequence[CandidateInput]) -> None:
        self._candidates = tuple(candidates)

    def fetch(self, niche: str) -> list[CandidateInput]:
        del niche
        return list(self._candidates)


class DeterministicEditorialProvider:
    """Stable editorial adapter; it does not call a model or external service."""

    def create_brief(self, candidate: CandidateInput) -> EditorialBrief:
        return EditorialBrief(
            topic=candidate.title,
            angle=f"Explicar de forma breve: {candidate.title}",
            audience="Audiencia general",
            promise="Entender el tema en menos de un minuto",
            key_points=(candidate.summary,),
            tone="claro",
            target_duration_seconds=30,
            source_urls=(str(candidate.canonical_url),),
        )

    def create_script(self, brief: EditorialBrief) -> VideoScript:
        point = brief.key_points[0]
        return VideoScript(
            title=brief.topic,
            hook=brief.promise,
            scenes=(
                ScriptScene(
                    order=1,
                    narration=brief.promise,
                    on_screen_text=brief.topic,
                    visual_direction="Título centrado sobre fondo sólido",
                    duration_seconds=5,
                ),
                ScriptScene(
                    order=2,
                    narration=point,
                    on_screen_text=point[:120],
                    visual_direction="Texto principal sobre fondo sólido",
                    duration_seconds=20,
                ),
                ScriptScene(
                    order=3,
                    narration="Eso es lo esencial.",
                    on_screen_text="Resumen completo",
                    visual_direction="Cierre limpio",
                    duration_seconds=5,
                ),
            ),
            closing="Eso es lo esencial.",
        )

