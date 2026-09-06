from short_video_generator.contracts import CandidateInput
from short_video_generator.providers.deterministic import (
    DeterministicEditorialProvider,
    FixtureSourceProvider,
)


def fixture_candidate() -> CandidateInput:
    return CandidateInput(
        external_id="fixture-1",
        title="Un solo tema",
        summary="Un resumen estable para el primer vertical slice.",
        canonical_url="https://example.test/tema",
    )


def test_fixture_source_returns_one_configured_candidate() -> None:
    candidate = fixture_candidate()
    provider = FixtureSourceProvider([candidate])
    assert provider.fetch("tecnologia") == [candidate]


def test_editorial_output_is_stable_and_contract_valid() -> None:
    provider = DeterministicEditorialProvider()
    candidate = fixture_candidate()

    first_brief = provider.create_brief(candidate)
    second_brief = provider.create_brief(candidate)
    script = provider.create_script(first_brief)

    assert first_brief == second_brief
    assert first_brief.topic == candidate.title
    assert len(script.scenes) == 3
    assert script.duration_seconds == 30
