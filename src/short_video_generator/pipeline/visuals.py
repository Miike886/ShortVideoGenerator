from dataclasses import dataclass

from short_video_generator.contracts import (
    ByteBeat,
    PresenterInstruction,
    SceneVisualDirection,
    ScriptScene,
    SemanticScenePlan,
    VisualSearchPlan,
)


@dataclass(frozen=True, slots=True)
class AssetCandidate:
    asset_id: str
    media_type: str
    width: int
    height: int
    duration_seconds: float | None = None
    source_quality: float = 0.0


def rank_candidates(
    candidates: tuple[AssetCandidate, ...],
    duration_seconds: float,
    preferred_media: str = "either",
    used_asset_ids: frozenset[str] = frozenset(),
) -> tuple[AssetCandidate, ...]:
    def score(candidate: AssetCandidate) -> tuple[float, str]:
        vertical = candidate.height / candidate.width if candidate.width else 0
        media = (
            1.0
            if preferred_media == "either" or candidate.media_type == preferred_media
            else 0.0
        )
        duration = 1.0 if candidate.duration_seconds is None else max(
            0.0, 1.0 - abs(candidate.duration_seconds - duration_seconds) / max(duration_seconds, 1)
        )
        duplicate = -3.0 if candidate.asset_id in used_asset_ids else 0.0
        return (
            media * 3 + min(vertical, 2.0) + duration + candidate.source_quality + duplicate,
            candidate.asset_id,
        )

    return tuple(sorted(candidates, key=score, reverse=True))


class DeterministicVisualPlanner:
    version = "visual-direction-v1"
    choreography_version = "byte-choreography-v1"
    ranking_version = "visual-ranking-v1"

    def plan(
        self,
        scene: ScriptScene,
        previous_region: str | None = None,
        semantic_scene: SemanticScenePlan | None = None,
    ) -> SceneVisualDirection:
        purpose = {
            "hook": "establish", "context": "explain", "fact": "reveal",
            "development": "demonstrate", "payoff": "react", "conclusion": "conclude",
        }.get(scene.role, "explain")
        text = f"{scene.visual_direction} {scene.narration}".lower()
        comparison = any(
            word in text for word in ("compare", "while", "versus", "otro", "one system")
        )
        if comparison:
            purpose = "compare"
        focal = "center_right" if scene.order % 2 else "center_left"
        if purpose in {"establish", "conclude"}:
            focal = "center"
        if "strange" in text or "extrañ" in text or "surpris" in text:
            purpose = "reveal"
        action = {
            "establish": "greet", "explain": "explain", "demonstrate": "present_subject",
            "compare": "present_subject", "reveal": "react_surprised", "react": "react_surprised",
            "conclude": "conclude",
        }.get(purpose, "explain")
        if scene.role == "example":
            action = "present_subject"
        elif scene.role == "payoff":
            action = "conclude"
        if scene.role == "context":
            action = "think"
        if scene.role == "payoff" and scene.narration.lstrip().startswith(("Why ", "¿")):
            action = "question"
        if focal in {"center_right", "upper_right", "lower_right"}:
            facing = "right"
        elif focal in {"center_left", "upper_left", "lower_left"}:
            facing = "left"
        else:
            facing = "viewer"
        region = "lower_left" if facing == "right" else "lower_right"
        if previous_region and previous_region == region and purpose not in {"react", "reveal"}:
            entrance = "none"
        else:
            entrance = "fade"
        beats = ()
        if action == "present_subject":
            beats = (ByteBeat(progress=0.62, action="present_subject", target_direction=facing),)
        elif action == "react_surprised":
            beats = (ByteBeat(progress=0.58, action="react_surprised", target_direction="viewer"),)
        concept = semantic_scene.visual_concept if semantic_scene is not None else None
        subject = concept.subject if concept is not None else scene.visual_direction.strip()
        action_text = concept.observable_action if concept is not None else ""
        primary_query = (
            f"{subject} {action_text}".strip()
            if concept is not None
            else scene.visual_query.strip() or subject
        )
        return SceneVisualDirection(
            purpose=purpose,
            subject=subject,
            focal_region=focal,
            composition="compare_sides" if comparison else "support_subject",
            motion="slow_zoom_in" if scene.order % 2 else "pan_right",
            byte_action=action,
            byte_region=region,
            byte_facing=facing,
            entrance=entrance,
            exit="none",
            beats=beats,
            search=VisualSearchPlan(
                primary_query=primary_query,
                alternatives=(subject, action_text) if action_text else (subject,),
                avoid_terms=(
                    concept.avoid_concepts
                    if concept is not None
                    else ("abstract AI", "business meeting")
                ),
                preferred_media="either",
                visual_intent=purpose,
                visual_subject=subject,
                observable_action=action_text,
                scene_role=scene.role,
            ),
        )


def presenter_for_direction(
    direction: SceneVisualDirection, character_id: str, scale: float = 0.32
) -> PresenterInstruction:
    action_to_pose = {
        "greet": "explaining", "explain": "explaining", "present_subject": "pointing_right",
        "inspect": "thinking", "think": "thinking", "question": "skeptical",
        "react_surprised": "surprised", "react_skeptical": "skeptical", "celebrate": "happy",
        "shrug": "shrugging", "work": "working", "conclude": "happy", "idle": "neutral",
    }
    pose = action_to_pose.get(direction.byte_action, "neutral")
    if direction.byte_action == "present_subject" and direction.byte_facing == "left":
        pose = "pointing_left"
    position = {
        "lower_left": "bottom_left", "lower_right": "bottom_right", "center": "bottom_center",
    }.get(direction.byte_region, "bottom_right")
    entrance = "fade" if direction.entrance in {"fade", "pop"} else direction.entrance
    return PresenterInstruction(
        character_id=character_id, pose=pose, position=position, scale=scale,
        entrance=entrance, exit="none",
        action=direction.byte_action,
        facing=direction.byte_facing,
        motion_preset=(
            "byte_present_left" if direction.byte_facing == "left" else "byte_present_right"
        ),
        beats=tuple(beat.model_dump(mode="json") for beat in direction.beats),
    )
