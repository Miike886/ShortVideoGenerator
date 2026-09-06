import asyncio
import importlib.metadata
import math
import wave
from array import array
from pathlib import Path

from short_video_generator.contracts import AudioArtifactMetadata, TextToSpeechOptions


class EdgeTextToSpeechProvider:
    """Online, keyless Edge speech adapter for manual real-provider runs."""

    provider_name = "edge-tts"
    output_suffix = ".mp3"
    output_media_type = "audio/mpeg"

    def __init__(self) -> None:
        self.provider_version = importlib.metadata.version("edge-tts")

    def synthesize(
        self,
        text: str,
        output_path: Path,
        language: str,
        options: TextToSpeechOptions,
    ) -> AudioArtifactMetadata:
        import edge_tts

        normalized = " ".join(text.split())
        if not normalized:
            raise ValueError("TTS text cannot be empty")
        voice = options.voice or _default_edge_voice(language)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        communication = edge_tts.Communicate(
            normalized,
            voice,
            rate=f"{options.rate * 10:+d}%",
            volume=f"{options.volume - 100:+d}%",
        )
        try:
            asyncio.run(communication.save(str(output_path)))
        except Exception as error:
            raise RuntimeError(f"Edge TTS synthesis failed: {error}") from error
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise RuntimeError("Edge TTS did not produce an audio file")
        return AudioArtifactMetadata(
            provider=self.provider_name,
            provider_version=self.provider_version,
            voice=voice,
            language=language,
        )


class FakeTextToSpeechProvider:
    """Text-dependent PCM fixture used by the local deterministic path and tests."""

    provider_name = "fake-text-tone"
    provider_version = "1"
    output_suffix = ".wav"
    output_media_type = "audio/wav"
    sample_rate = 16_000

    def __init__(self) -> None:
        self.calls = 0

    def synthesize(
        self,
        text: str,
        output_path: Path,
        language: str,
        options: TextToSpeechOptions,
    ) -> AudioArtifactMetadata:
        self.calls += 1
        normalized = " ".join(text.split())
        if not normalized:
            raise ValueError("TTS text cannot be empty")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        duration_seconds = max(3.0, len(normalized.split()) * 0.32)
        sample_count = round(self.sample_rate * duration_seconds)
        characters = tuple(ord(character) for character in normalized)
        amplitude = round(1_800 * (options.volume / 100))
        samples = array(
            "h",
            (
                self._sample(index, sample_count, characters, amplitude, options.rate)
                for index in range(sample_count)
            ),
        )
        with wave.open(str(output_path), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(self.sample_rate)
            audio.writeframes(samples.tobytes())
        return AudioArtifactMetadata(
            provider=self.provider_name,
            provider_version=self.provider_version,
            voice=options.voice,
            language=language,
            sample_rate=self.sample_rate,
            duration_seconds=sample_count / self.sample_rate,
        )

    def _sample(
        self,
        index: int,
        sample_count: int,
        characters: tuple[int, ...],
        amplitude: int,
        rate: int,
    ) -> int:
        position = index / sample_count
        character = characters[min(int(position * len(characters)), len(characters) - 1)]
        frequency = 150 + (character % 24) * 12 + rate * 3
        syllable_position = (index % round(self.sample_rate * 0.16)) / self.sample_rate
        envelope = max(0.0, math.sin(math.pi * syllable_position / 0.16))
        return int(
            amplitude * envelope * math.sin(2 * math.pi * frequency * index / self.sample_rate)
        )


def _default_edge_voice(language: str) -> str:
    normalized = language.lower()
    if normalized.startswith("es"):
        return "es-MX-DaliaNeural"
    if normalized.startswith("en"):
        return "en-US-AriaNeural"
    raise ValueError(
        f"No default Edge TTS voice configured for language {language!r}; set --tts-voice"
    )
