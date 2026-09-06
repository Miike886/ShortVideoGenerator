from pathlib import Path

from short_video_generator.contracts import (
    CaptionStyle,
    ScriptScene,
    VideoScript,
    WordTiming,
)
from short_video_generator.providers.captions import FakeCaptionAlignmentProvider
from short_video_generator.rendering.subtitles import AssSubtitleProvider, group_caption_words


def test_fake_alignment_uses_known_script_words_and_audio_duration() -> None:
    script = _script("One bright idea works.")

    result = FakeCaptionAlignmentProvider().align(Path("voice.wav"), script, 4.0)

    assert [word.word for word in result.words] == ["One", "bright", "idea", "works"]
    assert result.words[0].start_seconds == 0
    assert result.words[-1].end_seconds == 4.0


def test_caption_grouping_limits_words_and_preserves_timing() -> None:
    words = tuple(
        WordTiming(word=f"w{index}", start_seconds=index * 0.5, end_seconds=(index + 1) * 0.5)
        for index in range(7)
    )

    groups = group_caption_words(words, CaptionStyle(max_words_per_group=3))

    assert [len(group.words) for group in groups] == [3, 3, 1]
    assert groups[0].start_seconds == 0
    assert groups[-1].end_seconds == 3.5


def test_ass_generation_creates_progressive_active_word_events(tmp_path) -> None:
    words = (
        WordTiming(word="byte", start_seconds=0.0, end_seconds=0.4),
        WordTiming(word="explains", start_seconds=0.4, end_seconds=1.0),
        WordTiming(word="clearly", start_seconds=1.0, end_seconds=1.5),
    )

    draft = AssSubtitleProvider().create(_script("Byte explains clearly."), words, tmp_path)
    content = (tmp_path / draft.relative_path).read_text(encoding="utf-8")

    assert draft.relative_path == Path("subtitles.ass")
    assert draft.metadata["caption_group_count"] == 1
    assert "Dialogue:" in content
    assert r"{\c&H0000D7FF&}BYTE" in content
    assert "BYTE EXPLAINS CLEARLY" in content.replace(r"{\c&H0000D7FF&}", "").replace(
        r"{\c&H00FFFFFF&}", ""
    )


def _script(narration: str) -> VideoScript:
    return VideoScript(
        title="Fixture",
        hook="Hook",
        scenes=(
            ScriptScene(
                order=1,
                narration=narration,
                visual_direction="Background",
                duration_seconds=3,
            ),
        ),
        closing="Done",
    )
