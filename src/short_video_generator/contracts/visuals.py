from typing import Literal

from pydantic import Field

from .common import Contract

VisualPurpose = Literal[
    "establish", "explain", "demonstrate", "compare", "reveal", "emphasize",
    "react", "transition", "conclude",
]
FocalRegion = Literal[
    "center", "center_left", "center_right", "upper_left", "upper_right",
    "lower_left", "lower_right", "full_frame",
]
TargetDirection = Literal["left", "right", "center", "viewer", "none"]
MediaPreference = Literal["video", "image", "either"]
ByteAction = Literal[
    "idle", "greet", "explain", "present_subject", "inspect", "think", "question",
    "react_surprised", "react_skeptical", "celebrate", "shrug", "work", "conclude",
]
EntranceStyle = Literal["none", "fade", "slide_up", "slide_left", "slide_right", "pop"]
ExitStyle = Literal["none", "fade", "slide_down", "slide_left", "slide_right"]
MotionPreset = Literal["static", "slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right"]


class ByteBeat(Contract):
    progress: float = Field(ge=0, le=1)
    action: ByteAction
    target_direction: TargetDirection = "none"
    emphasis: float = Field(default=1.0, ge=0, le=1)

    def at_duration(self, duration_seconds: float) -> dict[str, object]:
        return {
            "time_seconds": round(self.progress * duration_seconds, 3),
            "progress": self.progress,
            "action": self.action,
            "target_direction": self.target_direction,
            "emphasis": self.emphasis,
        }


class VisualSearchPlan(Contract):
    primary_query: str = Field(min_length=1, max_length=500)
    alternatives: tuple[str, ...] = ()
    avoid_terms: tuple[str, ...] = ()
    preferred_media: MediaPreference = "either"
    visual_intent: VisualPurpose = "explain"


class SceneVisualDirection(Contract):
    version: str = "visual-direction-v1"
    purpose: VisualPurpose = "explain"
    subject: str = Field(min_length=1, max_length=500)
    focal_region: FocalRegion = "center"
    composition: str = "support_subject"
    motion: MotionPreset = "static"
    byte_action: ByteAction = "explain"
    byte_region: FocalRegion = "lower_right"
    byte_facing: TargetDirection = "viewer"
    entrance: EntranceStyle = "fade"
    exit: ExitStyle = "none"
    beats: tuple[ByteBeat, ...] = Field(default_factory=tuple, max_length=3)
    search: VisualSearchPlan

    def resolved_beats(self, duration_seconds: float) -> tuple[dict[str, object], ...]:
        return tuple(beat.at_duration(duration_seconds) for beat in self.beats)
