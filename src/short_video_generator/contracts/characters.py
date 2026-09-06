from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .audio import TextToSpeechOptions
from .common import Contract

PresenterPosition = Literal["bottom_left", "bottom_right", "bottom_center"]
PresenterMotion = Literal["fade", "none"]


class CharacterDefinition(Contract):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=500)
    version: str = Field(min_length=1, max_length=40)
    asset_directory: Path
    default_pose: str = Field(min_length=1, max_length=80)
    available_poses: tuple[str, ...] = Field(min_length=1)
    preferred_screen_position: PresenterPosition = "bottom_right"
    scale: float = Field(default=0.32, ge=0.1, le=0.6)
    voice: TextToSpeechOptions | None = None

    @field_validator("asset_directory")
    @classmethod
    def asset_directory_must_be_relative(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("character asset_directory must be relative")
        return value

    @model_validator(mode="after")
    def default_pose_must_exist(self) -> "CharacterDefinition":
        if self.default_pose not in self.available_poses:
            raise ValueError("character default_pose must be in available_poses")
        return self


class PresenterInstruction(Contract):
    character_id: str = Field(min_length=1, max_length=80)
    pose: str = Field(min_length=1, max_length=80)
    position: PresenterPosition | None = None
    scale: float | None = Field(default=None, ge=0.1, le=0.6)
    entrance: PresenterMotion = "fade"
    exit: PresenterMotion = "fade"


class CharacterAssetReference(Contract):
    scene_order: int = Field(ge=1)
    character_id: str = Field(min_length=1, max_length=80)
    character_name: str = Field(min_length=1, max_length=120)
    character_version: str = Field(min_length=1, max_length=40)
    pose: str = Field(min_length=1, max_length=80)
    asset_path: Path
    asset_relative_path: Path
    media_type: str = Field(default="image/png")
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    has_alpha: bool = True
    position: PresenterPosition
    scale: float = Field(ge=0.1, le=0.6)
    entrance: PresenterMotion = "fade"
    exit: PresenterMotion = "fade"
    fingerprint: str = Field(min_length=64, max_length=64)

    @field_validator("asset_relative_path")
    @classmethod
    def asset_relative_path_must_be_relative(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("character asset path must be relative")
        return value
