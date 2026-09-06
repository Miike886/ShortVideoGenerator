from typing import Literal

from pydantic import Field, model_validator

from .characters import PresenterInstruction
from .common import Contract

SceneRole = Literal["hook", "context", "fact", "development", "payoff", "conclusion"]


class EditorialBrief(Contract):
    topic: str = Field(min_length=1, max_length=300)
    angle: str = Field(min_length=1, max_length=500)
    audience: str = Field(min_length=1, max_length=300)
    promise: str = Field(min_length=1, max_length=500)
    key_points: tuple[str, ...] = Field(min_length=1, max_length=7)
    tone: str = Field(min_length=1, max_length=100)
    target_duration_seconds: int = Field(ge=10, le=180)
    source_urls: tuple[str, ...] = Field(min_length=1)
    warnings: tuple[str, ...] = ()


class ScriptScene(Contract):
    order: int = Field(ge=1)
    narration: str = Field(min_length=1, max_length=2_000)
    on_screen_text: str = Field(default="", max_length=300)
    visual_direction: str = Field(min_length=1, max_length=1_000)
    visual_query: str = Field(default="", max_length=500)
    duration_seconds: float = Field(gt=0, le=60)
    presenter: PresenterInstruction | None = None
    role: SceneRole = "fact"


class VideoScript(Contract):
    title: str = Field(min_length=1, max_length=300)
    hook: str = Field(min_length=1, max_length=500)
    scenes: tuple[ScriptScene, ...] = Field(min_length=1, max_length=10)
    closing: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def scene_order_is_contiguous(self) -> "VideoScript":
        orders = [scene.order for scene in self.scenes]
        if orders != list(range(1, len(self.scenes) + 1)):
            raise ValueError("scene order must be contiguous and start at 1")
        return self

    @property
    def duration_seconds(self) -> float:
        return sum(scene.duration_seconds for scene in self.scenes)
