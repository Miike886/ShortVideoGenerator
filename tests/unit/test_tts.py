import hashlib
import wave

from short_video_generator.contracts import TextToSpeechOptions
from short_video_generator.providers.tts import FakeTextToSpeechProvider


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
