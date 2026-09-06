from short_video_generator.contracts import ScriptScene
from short_video_generator.pipeline.visuals import (
    AssetCandidate,
    DeterministicVisualPlanner,
    presenter_for_direction,
    rank_candidates,
)


def scene(
    role: str = "fact", order: int = 1, text: str = "A concrete visual subject"
) -> ScriptScene:
    return ScriptScene(
        order=order,
        narration=text,
        visual_direction="developer reviewing code warnings",
        visual_query="programmer debugging code",
        duration_seconds=5,
        role=role,
    )


def test_planner_is_deterministic_and_generates_direction_for_each_scene() -> None:
    planner = DeterministicVisualPlanner()
    scenes = [scene(role, index) for index, role in enumerate(
        ("hook", "context", "fact", "development", "conclusion"), 1
    )]
    first = [planner.plan(item).model_dump() for item in scenes]
    second = [planner.plan(item).model_dump() for item in scenes]
    assert first == second
    assert all(item["subject"] for item in first)
    assert {item["purpose"] for item in first} <= {
        "establish", "explain", "demonstrate", "compare", "reveal", "emphasize",
        "react", "transition", "conclude",
    }


def test_subject_side_drives_byte_presentation_pose_and_region() -> None:
    planner = DeterministicVisualPlanner()
    right = planner.plan(scene(role="development", order=1))
    left = planner.plan(scene(role="development", order=2))
    assert right.focal_region == "center_right"
    assert right.byte_region == "lower_left"
    assert presenter_for_direction(right, "byte").pose == "pointing_right"
    assert left.focal_region == "center_left"
    assert left.byte_region == "lower_right"
    assert presenter_for_direction(left, "byte").pose == "pointing_left"


def test_beats_resolve_against_actual_duration_without_changing_semantics() -> None:
    direction = DeterministicVisualPlanner().plan(scene(role="development", order=1))
    assert direction.beats[0].progress == 0.62
    assert direction.resolved_beats(5.0)[0]["time_seconds"] == 3.1
    assert direction.resolved_beats(10.0)[0]["time_seconds"] == 6.2


def test_continuity_avoids_reentering_when_region_is_unchanged() -> None:
    planner = DeterministicVisualPlanner()
    first = planner.plan(scene(role="development", order=1))
    second = planner.plan(scene(role="development", order=3), first.byte_region)
    assert second.byte_region == first.byte_region
    assert second.entrance == "none"


def test_candidate_ranking_penalizes_duplicates_and_prefers_vertical_media() -> None:
    candidates = (
        AssetCandidate("first", "video", 1920, 1080, 5),
        AssetCandidate("vertical", "video", 1080, 1920, 5),
        AssetCandidate("used", "video", 1080, 1920, 5),
    )
    ranked = rank_candidates(candidates, 5, used_asset_ids=frozenset({"used"}))
    assert ranked[0].asset_id == "vertical"
    assert ranked[-1].asset_id == "used"
