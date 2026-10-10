from short_video_generator.contracts import CandidateInput
from short_video_generator.providers.deterministic import DeterministicEditorialProvider


def test_deterministic_script_plans_structured_presenter_in_every_scene() -> None:
    provider = DeterministicEditorialProvider(character_id="byte")
    brief = provider.create_brief(
        CandidateInput(
            external_id="fixture",
            title="Docker",
            summary="Docker packages applications with their dependencies.",
            canonical_url="https://example.test/docker",
            source_payload={},
        )
    )

    script = provider.create_script(brief)

    assert [scene.role for scene in script.scenes] == [
        "hook",
        "context",
        "mechanism",
        "example",
        "payoff",
    ]
    assert len(script.scenes) == 5
    assert script.story_plan is not None
    assert script.story_plan.scenes[2].role == "mechanism"
    presenters = [scene.presenter for scene in script.scenes]
    assert all(presenter is not None for presenter in presenters)
    assert [presenter.pose for presenter in presenters if presenter is not None] == [
        "explaining",
        "thinking",
        "surprised",
        "pointing_left",
        "happy",
    ]
