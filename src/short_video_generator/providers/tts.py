import asyncio
import importlib.metadata
import logging
import math
import time
import wave
from array import array
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

from short_video_generator.contracts import AudioArtifactMetadata, TextToSpeechOptions

logger = logging.getLogger(__name__)


class ElevenLabsConfigurationError(ValueError):
    pass


class ElevenLabsProviderError(RuntimeError):
    pass


class ElevenLabsTextToSpeechProvider:
    """Optional ElevenLabs adapter; the SDK is imported only when this provider is used."""

    provider_name = "elevenlabs"
    output_suffix = ".mp3"
    output_media_type = "audio/mpeg"
    adapter_version = "1"

    def __init__(
        self,
        api_key: str | None,
        voice_id: str | None,
        model_id: str = "eleven_multilingual_v2",
        voice_version: str = "byte_voice_dev_v1",
        client: object | None = None,
        max_retries: int = 2,
        voice_settings_factory: Callable[..., object] | None = None,
    ) -> None:
        if not api_key:
            raise ElevenLabsConfigurationError(
                "ELEVENLABS_API_KEY is required when TTS_PROVIDER=elevenlabs."
            )
        if not voice_id:
            raise ElevenLabsConfigurationError(
                "ELEVENLABS_VOICE_ID is required when TTS_PROVIDER=elevenlabs."
            )
        self.voice_id = voice_id
        self.model_id = model_id
        self.voice_version = voice_version
        self.max_retries = max(0, max_retries)
        self.voice_settings_factory = voice_settings_factory
        self.provider_version = (
            f"elevenlabs-sdk-{_sdk_version(client)}-adapter-{self.adapter_version}"
        )
        if client is None:
            try:
                from elevenlabs.client import ElevenLabs
            except ImportError as error:
                raise ElevenLabsConfigurationError(
                    "Install the optional ElevenLabs dependency with "
                    "uv sync --extra elevenlabs."
                ) from error
            self.client = ElevenLabs(api_key=api_key)
        else:
            self.client = client

    def synthesize(
        self,
        text: str,
        output_path: Path,
        language: str,
        options: TextToSpeechOptions,
    ) -> AudioArtifactMetadata:
        normalized = " ".join(text.split())
        if not normalized:
            raise ValueError("TTS text cannot be empty")
        voice_id = options.voice or self.voice_id
        model_id = options.model_id or self.model_id
        voice_settings = self._voice_settings(options)
        request = {
            "text": normalized,
            "voice_id": voice_id,
            "model_id": model_id,
            "output_format": "mp3_44100_128",
            "voice_settings": voice_settings,
        }
        if not model_id.endswith("multilingual_v2"):
            request["language_code"] = language[:2].lower()
        logger.info(
            "ElevenLabs TTS selected model=%s voice_version=%s characters=%d",
            model_id,
            options.voice_version or self.voice_version,
            len(normalized),
        )
        started = time.monotonic()
        response = self._request(request)
        audio_data = getattr(response, "data", None)
        if not isinstance(audio_data, bytes) or not audio_data:
            raise ElevenLabsProviderError("ElevenLabs returned an empty audio response")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio_data)
        elapsed = time.monotonic() - started
        headers = getattr(response, "headers", {})
        request_id = headers.get("request-id")
        character_cost = _int_header(headers.get("character-cost"))
        logger.info(
            "ElevenLabs TTS completed request_id=%s elapsed_seconds=%.3f characters=%d",
            request_id or "unavailable",
            elapsed,
            len(normalized),
        )
        return AudioArtifactMetadata(
            provider=self.provider_name,
            provider_version=self.provider_version,
            voice=voice_id,
            language=language,
            request_id=request_id,
            character_count=len(normalized),
            character_cost=character_cost,
            output_format="mp3_44100_128",
            request_duration_seconds=elapsed,
        )

    def _request(self, request: dict[str, object]) -> object:
        for attempt in range(self.max_retries + 1):
            try:
                raw_response = self.client.text_to_speech.with_raw_response.convert(
                    **request
                )
                if hasattr(raw_response, "__enter__"):
                    with raw_response as response:
                        return _materialize_response(response)
                return _materialize_response(raw_response)
            except Exception as error:
                status_code = _status_code(error)
                transient = status_code == 429 or status_code is not None and status_code >= 500
                if not transient or attempt >= self.max_retries:
                    if status_code in {401, 403}:
                        raise ElevenLabsProviderError(
                            "ElevenLabs rejected the API key; check ELEVENLABS_API_KEY."
                        ) from error
                    if status_code == 404 or status_code == 422:
                        raise ElevenLabsProviderError(
                            "ElevenLabs rejected the voice or request; check "
                            "ELEVENLABS_VOICE_ID and generation settings."
                        ) from error
                    if status_code == 429:
                        raise ElevenLabsProviderError(
                            "ElevenLabs rate limit or quota reached; try again later."
                        ) from error
                    raise ElevenLabsProviderError(
                        "ElevenLabs narration request failed; inspect provider availability "
                        "and configuration."
                    ) from error
                time.sleep(0.25 * (2**attempt))
        raise AssertionError("unreachable")

    def _voice_settings(self, options: TextToSpeechOptions) -> object:
        values = {
            "stability": options.stability if options.stability is not None else 0.5,
            "similarity_boost": (
                options.similarity_boost if options.similarity_boost is not None else 0.75
            ),
            "style": options.style if options.style is not None else 0.0,
            "use_speaker_boost": (
                options.use_speaker_boost
                if options.use_speaker_boost is not None
                else True
            ),
            "speed": options.speed if options.speed is not None else 1.0,
        }
        if self.voice_settings_factory is not None:
            return self.voice_settings_factory(**values)
        try:
            from elevenlabs import VoiceSettings
        except ImportError as error:
            raise ElevenLabsConfigurationError(
                "Install the optional ElevenLabs dependency with uv sync --extra elevenlabs."
            ) from error
        return VoiceSettings(**values)


def _sdk_version(client: object | None) -> str:
    if client is not None:
        return "mock"
    try:
        return importlib.metadata.version("elevenlabs")
    except importlib.metadata.PackageNotFoundError:
        return "uninstalled"


def _status_code(error: Exception) -> int | None:
    value = getattr(error, "status_code", None)
    if value is None:
        response = getattr(error, "response", None)
        value = getattr(response, "status_code", None)
    return value if isinstance(value, int) else None


def _int_header(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _materialize_response(response: object) -> object:
    data = getattr(response, "data", None)
    if isinstance(data, bytes):
        audio_data = data
    else:
        try:
            audio_data = b"".join(data)
        except TypeError as error:
            raise ElevenLabsProviderError(
                "ElevenLabs returned an invalid audio response"
            ) from error
    return SimpleNamespace(data=audio_data, headers=getattr(response, "headers", {}))


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
