from decimal import Decimal

from short_video_generator.contracts import ScriptScene, VideoScript
from short_video_generator.pipeline.timeline import fit_script_to_audio


def test_timeline_uses_audio_duration_and_preserves_three_scene_texts() -> None:
    script = VideoScript(
        title="Narrated fixture",
        hook="Hook",
        scenes=tuple(
            ScriptScene(
                order=index,
                narration=narration,
                visual_direction=f"Background {index}",
                duration_seconds=10,
            )
            for index, narration in enumerate(
                ("One", "Two words", "Three narration words"), start=1
            )
        ),
        closing="Closing",
    )

    fitted = fit_script_to_audio(script, 10.001)

    durations = [Decimal(str(scene.duration_seconds)) for scene in fitted.scenes]
    assert durations == [Decimal("1.667"), Decimal("3.334"), Decimal("5.000")]
    assert sum(durations) == Decimal("10.001")
    assert [scene.narration for scene in fitted.scenes] == [
        scene.narration for scene in script.scenes
    ]


def test_timeline_accepts_a_single_scene() -> None:
    script = VideoScript(
        title="Invalid fixture",
        hook="Hook",
        scenes=(
            ScriptScene(
                order=1,
                narration="Only scene",
                visual_direction="Background",
                duration_seconds=3,
            ),
        ),
        closing="Closing",
    )

    fitted = fit_script_to_audio(script, 3)

    assert fitted.scenes[0].duration_seconds == 3
