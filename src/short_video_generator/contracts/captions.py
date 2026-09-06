from pydantic import Field, model_validator

from .common import Contract


class WordTiming(Contract):
    word: str = Field(min_length=1, max_length=80)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def end_must_follow_start(self) -> "WordTiming":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("word timing end must follow start")
        return self


class CaptionAlignmentResult(Contract):
    words: tuple[WordTiming, ...] = Field(min_length=1)
    duration_seconds: float = Field(gt=0)
    provider: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)


class CaptionGroup(Contract):
    words: tuple[WordTiming, ...] = Field(min_length=1, max_length=5)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def group_bounds_must_contain_words(self) -> "CaptionGroup":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("caption group end must follow start")
        if self.words[0].start_seconds < self.start_seconds:
            raise ValueError("caption group starts after first word")
        if self.words[-1].end_seconds > self.end_seconds:
            raise ValueError("caption group ends before final word")
        return self


class CaptionStyle(Contract):
    max_words_per_group: int = Field(default=3, ge=2, le=5)
    max_group_duration_seconds: float = Field(default=2.2, gt=0)
    font_size: int = Field(default=64, ge=24, le=120)
    bottom_margin: int = Field(default=430, ge=120, le=900)
    outline_width: int = Field(default=4, ge=0, le=12)
    shadow: int = Field(default=1, ge=0, le=4)
    active_word_emphasis: bool = True
