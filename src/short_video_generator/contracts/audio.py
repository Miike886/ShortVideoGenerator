from pydantic import Field

from .common import Contract


class TextToSpeechOptions(Contract):
    voice: str | None = Field(default=None, max_length=200)
    rate: int = Field(default=0, ge=-10, le=10)
    volume: int = Field(default=100, ge=0, le=100)


class AudioArtifactMetadata(Contract):
    provider: str = Field(min_length=1, max_length=100)
    provider_version: str = Field(min_length=1, max_length=100)
    voice: str | None = Field(default=None, max_length=200)
    language: str = Field(min_length=2, max_length=20)
    sample_rate: int | None = Field(default=None, gt=0)
    duration_seconds: float | None = Field(default=None, gt=0)


class AudioProbeResult(Contract):
    duration_seconds: float = Field(gt=0)
    codec_name: str = Field(min_length=1, max_length=100)
    sample_rate: int | None = Field(default=None, gt=0)
