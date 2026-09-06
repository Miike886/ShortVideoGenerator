from short_video_generator.contracts import CandidateInput
from short_video_generator.providers.deterministic import DeterministicEditorialProvider


def test_deterministic_script_plans_reusable_presenter_in_two_scenes() -> None:
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

    presenters = [scene.presenter for scene in script.scenes]
    assert presenters[0] is not None
    assert presenters[0].character_id == "byte"
    assert presenters[0].pose == "explaining"
    assert presenters[1] is None
    assert presenters[2] is not None
    assert presenters[2].pose == "happy"
