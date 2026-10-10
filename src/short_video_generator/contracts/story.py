from typing import Literal

from pydantic import Field, model_validator

from .common import Contract

SemanticSceneRole = Literal[
    "hook", "context", "mechanism", "example", "evidence", "contrast",
    "implication", "payoff", "conclusion", "cta",
]
SceneRelation = Literal[
    "introduces", "clarifies", "explains", "exemplifies", "contrasts",
    "deepens", "resolves", "applies", "concludes",
]
VisualRepresentation = Literal["real_world", "ui", "diagram", "text", "character_led", "flexible"]
VisualSpecificity = Literal["concrete", "moderate", "abstract"]


class VisualConcept(Contract):
    subject: str = Field(min_length=3, max_length=300)
    observable_action: str = Field(min_length=3, max_length=300)
    environment: str = Field(min_length=2, max_length=200)
    supporting_objects: tuple[str, ...] = Field(default_factory=tuple, max_length=6)
    visual_goal: str = Field(min_length=3, max_length=300)
    preferred_representation: VisualRepresentation = "real_world"
    specificity: VisualSpecificity = "concrete"
    avoid_concepts: tuple[str, ...] = Field(default_factory=tuple, max_length=8)


class SemanticScenePlan(Contract):
    order: int = Field(ge=1)
    role: SemanticSceneRole
    communicative_goal: str = Field(min_length=3, max_length=400)
    new_information: str = Field(min_length=3, max_length=500)
    relation_to_previous: SceneRelation
    viewer_learns: str = Field(min_length=3, max_length=500)
    narration: str = Field(min_length=3, max_length=2_000)
    visual_concept: VisualConcept


class SemanticStoryPlan(Contract):
    version: str = "semantic-story-plan-v1"
    topic: str = Field(min_length=3, max_length=300)
    central_claim: str = Field(min_length=5, max_length=500)
    scenes: tuple[SemanticScenePlan, ...] = Field(min_length=2, max_length=10)

    @model_validator(mode="after")
    def scene_orders_are_contiguous(self) -> "SemanticStoryPlan":
        orders = [scene.order for scene in self.scenes]
        if orders != list(range(1, len(self.scenes) + 1)):
            raise ValueError("semantic scene order must be contiguous and start at 1")
        if self.scenes[0].role != "hook":
            raise ValueError("semantic story must start with a hook")
        if not any(scene.role in {"mechanism", "evidence", "example"} for scene in self.scenes):
            raise ValueError("semantic story must explain or concretize the central claim")
        if self.scenes[-1].role not in {"payoff", "conclusion", "cta"}:
            raise ValueError("semantic story must end with a payoff, conclusion or CTA")
        return self

    def redundancy_warnings(self) -> tuple[str, ...]:
        normalized = [_normalize(scene.new_information) for scene in self.scenes]
        warnings: list[str] = []
        for index, value in enumerate(normalized):
            if value == _normalize(self.central_claim):
                warnings.append(f"scene {index + 1} restates the central claim")
            if value and value in normalized[:index]:
                warnings.append(f"scene {index + 1} repeats earlier new_information")
        return tuple(warnings)

    def validate_progression(self) -> tuple[str, ...]:
        warnings = list(self.redundancy_warnings())
        for scene in self.scenes[1:]:
            if not scene.new_information.strip():
                warnings.append(f"scene {scene.order} has no new information")
            if scene.visual_concept.specificity == "abstract":
                warnings.append(f"scene {scene.order} visual concept is abstract")
        return tuple(warnings)

    def debug_text(self) -> str:
        lines = [f"CENTRAL CLAIM: {self.central_claim}"]
        for scene in self.scenes:
            lines.extend(
                (
                    f"\nSCENE {scene.order}",
                    f"Role: {scene.role}",
                    f"Goal: {scene.communicative_goal}",
                    f"New information: {scene.new_information}",
                    f"Relation: {scene.relation_to_previous}",
                    f"Viewer learns: {scene.viewer_learns}",
                    f"Narration: {scene.narration}",
                    f"Visual concept: {scene.visual_concept.subject}",
                    f"Observable action: {scene.visual_concept.observable_action}",
                )
            )
        return "\n".join(lines)


def _normalize(value: str) -> str:
    return " ".join(value.lower().replace(".", "").split())
