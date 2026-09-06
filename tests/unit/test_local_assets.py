import hashlib
from pathlib import Path

from short_video_generator.contracts import (
    ScriptScene,
    TextToSpeechOptions,
    VideoScript,
    WordTiming,
)
from short_video_generator.providers.assets import FakeAssetProvider
from short_video_generator.providers.tts import FakeTextToSpeechProvider
from short_video_generator.rendering.subtitles import AssSubtitleProvider
from short_video_generator.storage import LocalArtifactStore


def script_fixture() -> VideoScript:
    return VideoScript(
        title="Fixture",
        hook="Inicio",
        scenes=(
            ScriptScene(
                order=1,
                narration="Primera escena.",
                visual_direction="Fondo uno",
                duration_seconds=5,
            ),
            ScriptScene(
                order=2,
                narration="Segunda escena.",
                visual_direction="Fondo dos",
                duration_seconds=20,
            ),
            ScriptScene(
                order=3,
                narration="Tercera escena.",
                visual_direction="Fondo tres",
                duration_seconds=5,
            ),
        ),
        closing="Fin",
    )


def test_media_audio_and_subtitles_are_local_and_reproducible(tmp_path) -> None:
    script = script_fixture()
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_provider = FakeAssetProvider()
    second_provider = FakeAssetProvider()
    first_images = [
        first_provider.acquire(f"query {scene.order}", scene.order, first)
        for scene in script.scenes
    ]
    second_images = [
        second_provider.acquire(f"query {scene.order}", scene.order, second)
        for scene in script.scenes
    ]
    provider = FakeTextToSpeechProvider()
    first_audio_path = first / "voice.wav"
    second_audio_path = second / "voice.wav"
    first_audio = provider.synthesize(
        "fixture narration", first_audio_path, "en", TextToSpeechOptions()
    )
    second_audio = provider.synthesize(
        "fixture narration", second_audio_path, "en", TextToSpeechOptions()
    )
    words = (
        WordTiming(word="Primera", start_seconds=0, end_seconds=0.5),
        WordTiming(word="escena", start_seconds=0.5, end_seconds=1.0),
    )
    subtitle = AssSubtitleProvider().create(script, words, first)

    assert len(first_images) == len(script.scenes) == 3
    assert Path(subtitle.relative_path).suffix == ".ass"
    assert "Dialogue:" in (first / subtitle.relative_path).read_text(encoding="utf-8")
    assert _sha256(first / first_images[0].relative_path) == _sha256(
        second / second_images[0].relative_path
    )
    assert first_audio.provider == provider.provider_name
    assert first_audio.duration_seconds == second_audio.duration_seconds
    assert _sha256(first_audio_path) == _sha256(second_audio_path)


def test_artifact_store_promotes_work_without_leaving_partial_files(tmp_path) -> None:
    store = LocalArtifactStore(tmp_path / "storage")
    work = store.prepare_work_directory("run-1")
    source = work / "asset.txt"
    source.write_text("deterministic", encoding="utf-8")

    stored = store.promote(source, store.asset_directory("production-1") / source.name)

    assert stored.absolute_path.read_text(encoding="utf-8") == "deterministic"
    assert stored.relative_path.as_posix() == "assets/production-1/asset.txt"
    assert not stored.absolute_path.with_suffix(".txt.partial").exists()


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
