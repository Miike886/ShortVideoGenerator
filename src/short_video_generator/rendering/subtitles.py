from datetime import timedelta
from pathlib import Path

from short_video_generator.contracts import LocalFileDraft, VideoScript
from short_video_generator.domain.enums import ArtifactType


class BasicSubtitleProvider:
    def create(self, script: VideoScript, destination: Path) -> LocalFileDraft:
        return create_srt(script, destination)


def create_srt(script: VideoScript, destination: Path) -> LocalFileDraft:
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / "subtitles.srt"
    elapsed = 0.0
    blocks: list[str] = []
    for scene in script.scenes:
        start = _srt_timestamp(elapsed)
        elapsed += scene.duration_seconds
        end = _srt_timestamp(elapsed)
        narration = scene.narration.replace("\n", " ").strip()
        blocks.append(f"{scene.order}\n{start} --> {end}\n{narration}\n")
    output.write_text("\n".join(blocks), encoding="utf-8")
    return LocalFileDraft(
        artifact_type=ArtifactType.SUBTITLE,
        relative_path=Path(output.name),
        media_type="application/x-subrip",
        metadata={"duration_seconds": elapsed},
    )


def _srt_timestamp(seconds: float) -> str:
    value = timedelta(seconds=seconds)
    total_milliseconds = int(value.total_seconds() * 1_000)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"
