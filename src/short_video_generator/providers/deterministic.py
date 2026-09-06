import math
import wave
from array import array
from collections.abc import Sequence
from pathlib import Path

from short_video_generator.contracts import (
    CandidateInput,
    EditorialBrief,
    LocalFileDraft,
    ScriptScene,
    VideoScript,
)
from short_video_generator.domain.enums import ArtifactType


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


class DeterministicSpeechProvider:
    sample_rate = 16_000
    frequency_hz = 440

    def synthesize(self, text: str, destination: Path) -> LocalFileDraft:
        del text
        destination.mkdir(parents=True, exist_ok=True)
        output = destination / "voice.wav"
        duration_seconds = 30
        amplitude = 2_000
        samples = array(
            "h",
            (
                int(
                    amplitude * math.sin(2 * math.pi * self.frequency_hz * index / self.sample_rate)
                )
                for index in range(self.sample_rate * duration_seconds)
            ),
        )
        with wave.open(str(output), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(self.sample_rate)
            audio.writeframes(samples.tobytes())
        return LocalFileDraft(
            artifact_type=ArtifactType.VOICE,
            relative_path=Path(output.name),
            media_type="audio/wav",
            metadata={"duration_seconds": duration_seconds, "fixture": True},
        )


class DeterministicMediaProvider:
    width = 540
    height = 960
    colors = ((31, 41, 55), (30, 64, 175), (88, 28, 135), (6, 95, 70), (153, 27, 27))

    def create_visuals(self, script: VideoScript, destination: Path) -> list[LocalFileDraft]:
        destination.mkdir(parents=True, exist_ok=True)
        assets: list[LocalFileDraft] = []
        for scene, color in zip(script.scenes, self.colors, strict=False):
            filename = f"scene-{scene.order:02d}.ppm"
            output = destination / filename
            header = f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
            output.write_bytes(header + bytes(color) * (self.width * self.height))
            assets.append(
                LocalFileDraft(
                    artifact_type=ArtifactType.IMAGE,
                    relative_path=Path(filename),
                    media_type="image/x-portable-pixmap",
                    metadata={"scene_order": scene.order, "fixture": True},
                )
            )
        return assets
