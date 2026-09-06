from pathlib import Path
from types import SimpleNamespace

from short_video_generator.contracts import (
    CharacterAssetReference,
    GeneratedAsset,
    PresenterInstruction,
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
                presenter=(
                    PresenterInstruction(character_id="byte", pose="explaining")
                    if index == 1
                    else None
                ),
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
            media_type="text/x-ssa",
        ),
    )

    presenter_path = tmp_path / "byte.png"
    presenter_path.write_text("fixture", encoding="utf-8")
    FfmpegRenderer(executable, tmp_path).render(
        RenderRequest(
            production_id="production",
            script=script,
            assets=assets,
            character_assets=(
                CharacterAssetReference(
                    scene_order=1,
                    character_id="byte",
                    character_name="Byte",
                    character_version="byte-v1",
                    pose="explaining",
                    asset_path=presenter_path,
                    asset_relative_path=Path("assets/characters/byte/explaining.png"),
                    width=360,
                    height=560,
                    position="bottom_right",
                    scale=0.32,
                    fingerprint="a" * 64,
                ),
            ),
        ),
        tmp_path / "work",
    )

    command = captured["command"]
    filter_complex = command[command.index("-filter_complex") + 1]
    assert "-stream_loop" in command
    assert "force_original_aspect_ratio=increase" in filter_complex
    assert "crop=1080:1920" in filter_complex
    assert "trim=duration=2.0" in filter_complex
    assert str(presenter_path) in command
    assert "format=rgba" in filter_complex
    assert "fade=t=in" in filter_complex
    assert "overlay=x=W-w-72:y=H-h-320" in filter_complex
    assert "subtitles=" in filter_complex
    assert "force_style" not in filter_complex
