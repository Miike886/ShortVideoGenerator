import os
import shutil
from pathlib import Path

import pytest

from short_video_generator.bootstrap import build_manual_pipeline
from short_video_generator.config import Settings
from short_video_generator.contracts import ManualProductionInput
from short_video_generator.pipeline.media_workflow import CachedNarrationError
from short_video_generator.providers.assets import FakeAssetProvider
from short_video_generator.providers.characters import LocalCharacterAssetProvider
from short_video_generator.providers.tts import FakeTextToSpeechProvider


def test_tts_modes_reuse_and_block_external_generation(tmp_path) -> None:
    live_settings = _settings(tmp_path, "live")
    live_tts = FakeTextToSpeechProvider()
    text = "Byte explica un flujo reutilizable."
    live_pipeline = _pipeline(live_settings, live_tts)

    generated = live_pipeline.execute_tts_reference("byte-reference", text)
    assert not generated.reused
    assert live_tts.calls == 1
    live_reused = live_pipeline.execute_tts_reference("byte-reference", text)
    assert live_reused.reused
    assert live_tts.calls == 1

    cached_tts = FakeTextToSpeechProvider()
    cached_pipeline = _pipeline(_settings(tmp_path, "cached"), cached_tts)
    reused = cached_pipeline.execute_tts_reference("byte-reference", text)
    assert reused.reused
    assert cached_tts.calls == 0

    with pytest.raises(CachedNarrationError, match="TTS_MODE=cached"):
        cached_pipeline.execute_tts_reference("byte-reference-miss", text)
    assert cached_tts.calls == 0


def test_cached_mode_rejects_missing_audio_file(tmp_path) -> None:
    text = "Byte conserva la misma voz."
    live_tts = FakeTextToSpeechProvider()
    generated = _pipeline(_settings(tmp_path, "live"), live_tts).execute_tts_reference(
        "byte-reference-missing", text
    )
    (tmp_path / "storage" / generated.artifact.relative_path).unlink()

    cached_tts = FakeTextToSpeechProvider()
    with pytest.raises(CachedNarrationError, match="missing or invalid"):
        _pipeline(_settings(tmp_path, "cached"), cached_tts).execute_tts_reference(
            "byte-reference-missing", text
        )
    assert cached_tts.calls == 0


def test_cached_mode_rejects_corrupt_audio_file(tmp_path) -> None:
    text = "Byte conserva la misma identidad."
    live_tts = FakeTextToSpeechProvider()
    generated = _pipeline(_settings(tmp_path, "live"), live_tts).execute_tts_reference(
        "byte-reference-corrupt", text
    )
    path = tmp_path / "storage" / generated.artifact.relative_path
    path.write_bytes(b"not-audio")

    cached_tts = FakeTextToSpeechProvider()
    with pytest.raises(CachedNarrationError, match="missing or invalid"):
        _pipeline(_settings(tmp_path, "cached"), cached_tts).execute_tts_reference(
            "byte-reference-corrupt", text
        )
    assert cached_tts.calls == 0


def _pipeline(settings: Settings, tts: FakeTextToSpeechProvider):
    return build_manual_pipeline(
        settings,
        ManualProductionInput(topic="Byte Voice v1 reference", language="en"),
        tts_provider=tts,
        asset_provider=FakeAssetProvider(),
        character_provider=LocalCharacterAssetProvider(Path("assets/characters")),
    )


def _settings(tmp_path: Path, tts_mode: str) -> Settings:
    return Settings(
        project_root=tmp_path,
        database_path=tmp_path / "data" / "app.db",
        storage_root=tmp_path / "storage",
        ffmpeg_path=_required_executable("SVG_FFMPEG_PATH", "ffmpeg"),
        ffprobe_path=_required_executable("SVG_FFPROBE_PATH", "ffprobe"),
        tts_mode=tts_mode,
    )


def _required_executable(environment_name: str, command: str) -> Path:
    configured = os.environ.get(environment_name)
    discovered = configured or shutil.which(command)
    if not discovered:
        pytest.skip(f"{command} is not installed or configured")
    path = Path(discovered).resolve()
    if not path.is_file():
        pytest.skip(f"{command} executable does not exist: {path}")
    return path
