from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from short_video_generator.contracts import (
    CandidateInput,
    GeneratedAsset,
    ReviewSubmission,
    ScriptScene,
    ValidationCheck,
    ValidationReport,
    VideoScript,
    VideoTemplate,
)
from short_video_generator.domain.enums import ArtifactType, ReviewDecision


def test_candidate_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        CandidateInput(
            external_id="fixture-1",
            title="Tema",
            summary="Resumen",
            canonical_url="https://example.test/tema",
            published_at=datetime.now(UTC),
            unexpected=True,
        )


def test_script_requires_contiguous_scene_order() -> None:
    with pytest.raises(ValidationError, match="contiguous"):
        VideoScript(
            title="Tema",
            hook="Gancho",
            scenes=(
                ScriptScene(
                    order=2,
                    narration="Texto",
                    visual_direction="Visual",
                    duration_seconds=5,
                ),
            ),
            closing="Fin",
        )


def test_validation_result_must_match_blocking_checks() -> None:
    with pytest.raises(ValidationError, match="blocking checks"):
        ValidationReport(
            checks=(ValidationCheck(name="audio", passed=False, blocking=True),),
            passed=True,
        )


def test_minimal_template_is_vertical() -> None:
    template = VideoTemplate()
    assert template.width == 1080
    assert template.height == 1920
    assert template.height > template.width


def test_non_approval_review_requires_feedback() -> None:
    with pytest.raises(ValidationError, match="comment is required"):
        ReviewSubmission(decision=ReviewDecision.CHANGES_REQUESTED)


def test_artifact_paths_cannot_escape_local_storage() -> None:
    with pytest.raises(ValidationError, match="cannot traverse"):
        GeneratedAsset(
            artifact_type=ArtifactType.RENDER,
            relative_path=Path("..") / "outside.mp4",
            media_type="video/mp4",
        )
