from pathlib import Path

from pydantic import Field, field_validator

from short_video_generator.domain.enums import ArtifactType

from .common import Contract
from .editorial import VideoScript


class GeneratedAsset(Contract):
    artifact_type: ArtifactType
    relative_path: Path
    media_type: str = Field(min_length=1, max_length=100)
    metadata: dict[str, object] = Field(default_factory=dict)

    @field_validator("relative_path")
    @classmethod
    def path_must_stay_inside_storage(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("artifact path must be relative and cannot traverse parents")
        return value


class VideoTemplate(Contract):
    name: str = "minimal_vertical"
    width: int = Field(default=1080, gt=0)
    height: int = Field(default=1920, gt=0)
    frames_per_second: int = Field(default=30, ge=1, le=120)
    background_color: str = Field(default="#111111", pattern=r"^#[0-9a-fA-F]{6}$")
    text_color: str = Field(default="#FFFFFF", pattern=r"^#[0-9a-fA-F]{6}$")


class RenderRequest(Contract):
    production_id: str = Field(min_length=1)
    script: VideoScript
    assets: tuple[GeneratedAsset, ...]
    template: VideoTemplate = Field(default_factory=VideoTemplate)


class RenderResult(Contract):
    render: GeneratedAsset
    duration_seconds: float = Field(gt=0)
