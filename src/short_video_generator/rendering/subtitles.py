from datetime import timedelta
from pathlib import Path

from short_video_generator.contracts import (
    CaptionGroup,
    CaptionStyle,
    LocalFileDraft,
    VideoScript,
    WordTiming,
)
from short_video_generator.domain.enums import ArtifactType


class AssSubtitleProvider:
    provider_name = "ass-dynamic-captions"
    provider_version = "progressive-word-v1"

    def __init__(self, style: CaptionStyle | None = None) -> None:
        self.style = style or CaptionStyle()

    def create(
        self,
        script: VideoScript,
        words: tuple[WordTiming, ...],
        destination: Path,
    ) -> LocalFileDraft:
        groups = group_caption_words(words, self.style)
        return create_ass(script, groups, self.style, destination)


def group_caption_words(
    words: tuple[WordTiming, ...], style: CaptionStyle | None = None
) -> tuple[CaptionGroup, ...]:
    active_style = style or CaptionStyle()
    groups: list[CaptionGroup] = []
    pending: list[WordTiming] = []
    for word in words:
        if pending and _should_break(pending, word, active_style):
            groups.append(_group(pending))
            pending = []
        pending.append(word)
    if pending:
        groups.append(_group(pending))
    return tuple(groups)


def create_ass(
    script: VideoScript,
    groups: tuple[CaptionGroup, ...],
    style: CaptionStyle,
    destination: Path,
) -> LocalFileDraft:
    del script
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / "subtitles.ass"
    output.write_text(_ass_document(groups, style), encoding="utf-8")
    duration = groups[-1].end_seconds if groups else 0
    return LocalFileDraft(
        artifact_type=ArtifactType.SUBTITLE,
        relative_path=Path(output.name),
        media_type="text/x-ssa",
        metadata={
            "duration_seconds": duration,
            "format": "ass",
            "provider": AssSubtitleProvider.provider_name,
            "provider_version": AssSubtitleProvider.provider_version,
            "caption_group_count": len(groups),
            "active_word_emphasis": style.active_word_emphasis,
        },
    )


def _should_break(pending: list[WordTiming], next_word: WordTiming, style: CaptionStyle) -> bool:
    if len(pending) >= style.max_words_per_group:
        return True
    duration = next_word.end_seconds - pending[0].start_seconds
    if duration > style.max_group_duration_seconds and len(pending) >= 2:
        return True
    return _has_phrase_break(pending[-1].word) and len(pending) >= 2


def _has_phrase_break(word: str) -> bool:
    return word.endswith((".", ",", ";", ":", "?", "!"))


def _group(words: list[WordTiming]) -> CaptionGroup:
    return CaptionGroup(
        words=tuple(words),
        start_seconds=words[0].start_seconds,
        end_seconds=words[-1].end_seconds,
    )


def _ass_document(groups: tuple[CaptionGroup, ...], style: CaptionStyle) -> str:
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        "Style: Default,Arial,"
        f"{style.font_size},&H00FFFFFF,&H0000D7FF,&H00202020,&H80000000,"
        f"-1,0,0,0,100,100,0,0,1,{style.outline_width},{style.shadow},2,80,80,"
        f"{style.bottom_margin},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for group in groups:
        lines.extend(_events_for_group(group, style))
    return "\n".join(lines) + "\n"


def _events_for_group(group: CaptionGroup, style: CaptionStyle) -> list[str]:
    events = []
    words = tuple(word.word.upper() for word in group.words)
    for index, timing in enumerate(group.words):
        start = _ass_timestamp(timing.start_seconds)
        end = _ass_timestamp(timing.end_seconds)
        text = _caption_text(words, index if style.active_word_emphasis else None)
        events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
    return events


def _caption_text(words: tuple[str, ...], active_index: int | None) -> str:
    parts = []
    for index, word in enumerate(words):
        escaped = _escape_ass_text(word)
        if active_index == index:
            parts.append(r"{\c&H0000D7FF&}" + escaped + r"{\c&H00FFFFFF&}")
        else:
            parts.append(escaped)
    return " ".join(parts)


def _escape_ass_text(value: str) -> str:
    return value.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def _ass_timestamp(seconds: float) -> str:
    value = timedelta(seconds=seconds)
    total_centiseconds = int(value.total_seconds() * 100)
    hours, remainder = divmod(total_centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    whole_seconds, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{centiseconds:02d}"
