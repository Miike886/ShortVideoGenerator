import pytest

from short_video_generator.contracts import (
    CandidateInput,
    SemanticScenePlan,
    SemanticStoryPlan,
    VisualConcept,
)
from short_video_generator.pipeline.story import DeterministicStoryPlanner
from short_video_generator.providers.deterministic import DeterministicEditorialProvider


def test_active_recall_fixture_progresses_from_question_to_payoff() -> None:
    brief = DeterministicEditorialProvider().create_brief(
        CandidateInput(
            external_id="active-recall",
            title="Why testing yourself helps memory",
            summary=(
                "Trying to retrieve information strengthens learning more effectively "
                "than rereading."
            ),
            canonical_url="https://example.test/active-recall",
        )
    )
    plan = DeterministicStoryPlanner().create(brief)
    assert plan.central_claim
    assert [scene.role for scene in plan.scenes] == [
        "hook", "context", "mechanism", "example", "payoff"
    ]
    assert all(scene.new_information for scene in plan.scenes[1:])
    assert all(scene.visual_concept.specificity == "concrete" for scene in plan.scenes)
    assert plan.scenes[2].relation_to_previous == "explains"
    assert plan.scenes[3].relation_to_previous == "exemplifies"
    assert "CENTRAL CLAIM" in plan.debug_text()
    assert "Observable action:" in plan.debug_text()


def test_redundant_story_is_flagged() -> None:
    concept = VisualConcept(
        subject="student answering a question",
        observable_action="pauses before checking notes",
        environment="desk",
        visual_goal="show recall",
    )
    scenes = tuple(
        SemanticScenePlan(
            order=index,
            role=("hook" if index == 1 else "mechanism" if index == 2 else "payoff"),
            communicative_goal="Explain the claim",
            new_information=(
                "Practice improves memory" if index != 2 else "Practice improves memory."
            ),
            relation_to_previous="introduces" if index == 1 else "explains",
            viewer_learns="Practice improves memory",
            narration="Practice helps.",
            visual_concept=concept,
        )
        for index in range(1, 4)
    )
    plan = SemanticStoryPlan(
        topic="Practice",
        central_claim="Practice improves memory",
        scenes=scenes,
    )
    assert plan.redundancy_warnings()


def test_visual_concept_requires_an_observable_action() -> None:
    with pytest.raises(ValueError):
        VisualConcept(
            subject="memory",
            observable_action="",
            environment="mind",
            visual_goal="show learning",
        )
