from pathlib import Path
from types import SimpleNamespace

from short_video_generator.contracts import (
    GeneratedAsset,
    RenderRequest,
    ScriptScene,
    VideoScript,
)
from short_video_generator.domain.enums import ArtifactType
from short_video_generator.rendering.ffmpeg import FfmpegRenderer


def test_renderer_loops_and_crops_video_assets(monkeypatch, tmp_path) -> None:
    executable = tmp_path / "ffmpeg.exe"
    executable.write_text("fixture", encoding="utf-8")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr("short_video_generator.rendering.ffmpeg.subprocess.run", fake_run)
    script = VideoScript(
        title="Fixture",
        hook="Hook",
        scenes=tuple(
            ScriptScene(
                order=index,
                narration=f"Scene {index}",
                visual_direction="Real asset",
                visual_query="developer laptop",
                duration_seconds=2,
            )
            for index in range(1, 4)
        ),
        closing="Done",
    )
    assets = tuple(
        GeneratedAsset(
            artifact_type=(ArtifactType.VIDEO_CLIP if index == 1 else ArtifactType.IMAGE),
            relative_path=Path(f"assets/scene-{index}.{'mp4' if index == 1 else 'jpg'}"),
            media_type=("video/mp4" if index == 1 else "image/jpeg"),
            metadata={"scene_order": index},
        )
        for index in range(1, 4)
    ) + (
        GeneratedAsset(
            artifact_type=ArtifactType.VOICE,
            relative_path=Path("assets/voice.mp3"),
            media_type="audio/mpeg",
        ),
        GeneratedAsset(
            artifact_type=ArtifactType.SUBTITLE,
            relative_path=Path("assets/subtitles.srt"),
            media_type="application/x-subrip",
        ),
    )

    FfmpegRenderer(executable, tmp_path).render(
        RenderRequest(production_id="production", script=script, assets=assets),
        tmp_path / "work",
    )

    command = captured["command"]
    filter_complex = command[command.index("-filter_complex") + 1]
    assert "-stream_loop" in command
    assert "force_original_aspect_ratio=increase" in filter_complex
    assert "crop=1080:1920" in filter_complex
    assert "trim=duration=2.0" in filter_complex
