from pydantic import Field

from .common import Contract


class TextToSpeechOptions(Contract):
    voice: str | None = Field(default=None, max_length=200)
    voice_version: str | None = Field(default=None, max_length=80)
    model_id: str | None = Field(default=None, max_length=100)
    rate: int = Field(default=0, ge=-10, le=10)
    volume: int = Field(default=100, ge=0, le=100)
    stability: float | None = Field(default=None, ge=0, le=1)
    similarity_boost: float | None = Field(default=None, ge=0, le=1)
    style: float | None = Field(default=None, ge=0, le=1)
    use_speaker_boost: bool | None = None
    speed: float | None = Field(default=None, ge=0.7, le=1.2)


class AudioArtifactMetadata(Contract):
    provider: str = Field(min_length=1, max_length=100)
    provider_version: str = Field(min_length=1, max_length=100)
    voice: str | None = Field(default=None, max_length=200)
    language: str = Field(min_length=2, max_length=20)
    sample_rate: int | None = Field(default=None, gt=0)
    duration_seconds: float | None = Field(default=None, gt=0)
    request_id: str | None = Field(default=None, max_length=200)
    character_count: int | None = Field(default=None, ge=0)
    character_cost: int | None = Field(default=None, ge=0)
    output_format: str | None = Field(default=None, max_length=80)
    request_duration_seconds: float | None = Field(default=None, ge=0)


class AudioProbeResult(Contract):
    duration_seconds: float = Field(gt=0)
    codec_name: str = Field(min_length=1, max_length=100)
    sample_rate: int | None = Field(default=None, gt=0)
