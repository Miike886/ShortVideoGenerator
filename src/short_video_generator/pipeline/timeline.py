from decimal import ROUND_HALF_UP, Decimal

from short_video_generator.contracts import ScriptScene, VideoScript


def fit_script_to_audio(script: VideoScript, duration_seconds: float) -> VideoScript:
    if len(script.scenes) != 3:
        raise ValueError("The narrated MVP timeline requires exactly three scenes")
    total = Decimal(str(duration_seconds)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    if total <= 0:
        raise ValueError("Audio duration must be positive")
    word_counts = tuple(Decimal(len(scene.narration.split())) for scene in script.scenes)
    total_words = sum(word_counts)
    if total_words <= 0:
        raise ValueError("Narrated scenes must contain words")
    first = (total * word_counts[0] / total_words).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP
    )
    second = (total * word_counts[1] / total_words).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP
    )
    durations = (first, second, total - first - second)
    scenes = tuple(
        ScriptScene(
            **scene.model_dump(exclude={"duration_seconds"}),
            duration_seconds=float(duration),
        )
        for scene, duration in zip(script.scenes, durations, strict=True)
    )
    return script.model_copy(update={"scenes": scenes})
