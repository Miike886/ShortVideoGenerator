import pytest

from short_video_generator.contracts import CandidateInput, ScriptScene, VideoScript
from short_video_generator.pipeline.editorial_gate import EditorialGate, EditorialGateError
from short_video_generator.providers.deterministic import DeterministicEditorialProvider


def test_editorial_gate_passes_a_progressive_story() -> None:
    provider = DeterministicEditorialProvider()
    candidate = CandidateInput(
        external_id="gate",
        title="Active recall",
        summary="Retrieving information strengthens learning.",
        canonical_url="https://example.test/gate",
    )
    script = provider.create_script(provider.create_brief(candidate))
    result = EditorialGate().validate(script)
    assert result.passed


def test_editorial_gate_rejects_missing_story_plan_before_media() -> None:
    script = VideoScript(
        title="Unvalidated",
        hook="A hook",
        scenes=(
            ScriptScene(
                order=1,
                narration="A scene",
                visual_direction="A concrete scene",
                duration_seconds=5,
                role="hook",
            ),
            ScriptScene(
                order=2,
                narration="An ending",
                visual_direction="A concrete ending",
                duration_seconds=5,
                role="conclusion",
            ),
        ),
        closing="An ending",
    )
    with pytest.raises(EditorialGateError, match="SemanticStoryPlan"):
        EditorialGate().validate(script)
