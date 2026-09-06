import hashlib
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from short_video_generator.bootstrap import _build_tts_provider
from short_video_generator.config import Settings
from short_video_generator.contracts import TextToSpeechOptions
from short_video_generator.pipeline.media_workflow import _fingerprint
from short_video_generator.providers.tts import (
    ElevenLabsConfigurationError,
    ElevenLabsTextToSpeechProvider,
    FakeTextToSpeechProvider,
)


def test_fake_tts_fulfills_contract_and_is_text_dependent(tmp_path) -> None:
    provider = FakeTextToSpeechProvider()
    options = TextToSpeechOptions(rate=1, volume=80)
    first = tmp_path / "first.wav"
    repeated = tmp_path / "repeated.wav"
    different = tmp_path / "different.wav"

    metadata = provider.synthesize("Texto narrado reproducible", first, "es", options)
    provider.synthesize("Texto narrado reproducible", repeated, "es", options)
    provider.synthesize("Un texto diferente y más largo", different, "es", options)

    with wave.open(str(first), "rb") as audio:
        observed_duration = audio.getnframes() / audio.getframerate()

    assert metadata.provider == provider.provider_name
    assert metadata.provider_version == provider.provider_version
    assert metadata.language == "es"
    assert metadata.duration_seconds == observed_duration
    assert _sha256(first) == _sha256(repeated)
    assert _sha256(first) != _sha256(different)


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_elevenlabs_requires_key_and_voice_id() -> None:
    with pytest.raises(ElevenLabsConfigurationError, match="ELEVENLABS_API_KEY"):
        ElevenLabsTextToSpeechProvider(None, "voice")
    with pytest.raises(ElevenLabsConfigurationError, match="ELEVENLABS_VOICE_ID"):
        ElevenLabsTextToSpeechProvider("key", None)


def test_elevenlabs_provider_uses_mocked_sdk_boundary(tmp_path) -> None:
    calls = []

    class Speech:
        def __init__(self) -> None:
            self.with_raw_response = self

        def convert(self, **request):
            calls.append(request)
            return SimpleNamespace(
                data=b"fake-mp3",
                headers={"request-id": "req-123", "character-cost": "42"},
            )

    provider = ElevenLabsTextToSpeechProvider(
        "key",
        "voice-123",
        client=SimpleNamespace(text_to_speech=Speech()),
        voice_settings_factory=lambda **values: values,
    )
    output = tmp_path / "voice.mp3"
    metadata = provider.synthesize(
        "  Hola   Byte  ",
        output,
        "es-MX",
        TextToSpeechOptions(voice_version="byte_voice_dev_v1"),
    )

    assert output.read_bytes() == b"fake-mp3"
    assert metadata.request_id == "req-123"
    assert metadata.character_count == 9
    assert metadata.character_cost == 42
    assert calls[0]["voice_id"] == "voice-123"
    assert calls[0]["model_id"] == "eleven_multilingual_v2"
    assert "language_code" not in calls[0]


def test_tts_provider_selection_is_explicit() -> None:
    settings = Settings(
        project_root=Path("."), database_path=Path("data/app.db"), storage_root=Path("storage")
    )
    assert _build_tts_provider(settings).provider_name == "fake-text-tone"


def test_tts_fingerprint_changes_only_for_tts_inputs() -> None:
    def fingerprint(text: str, options: TextToSpeechOptions) -> str:
        return _fingerprint(
            {
                "text": text,
                "options": options.model_dump(mode="json"),
                "provider": "elevenlabs",
                "provider_version": "elevenlabs-sdk-2.0-adapter-1",
                "language": "es",
            }
        )

    base = TextToSpeechOptions(
        voice="voice-1",
        voice_version="byte_voice_dev_v1",
        model_id="eleven_multilingual_v2",
        stability=0.5,
    )
    assert fingerprint("Texto original", base) == fingerprint("Texto original", base)
    assert fingerprint("Texto cambiado", base) != fingerprint("Texto original", base)
    assert fingerprint(
        "Texto original", base.model_copy(update={"voice": "voice-2"})
    ) != fingerprint("Texto original", base)
    assert fingerprint(
        "Texto original", base.model_copy(update={"voice_version": "byte_voice_v1"})
    ) != fingerprint("Texto original", base)
    assert fingerprint(
        "Texto original", base.model_copy(update={"model_id": "eleven_v3"})
    ) != fingerprint("Texto original", base)
    assert fingerprint(
        "Texto original", base.model_copy(update={"stability": 0.7})
    ) != fingerprint("Texto original", base)
