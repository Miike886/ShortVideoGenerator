from short_video_generator.contracts import CandidateInput
from short_video_generator.providers.evaluation import DeterministicCandidateEvaluator


def test_deterministic_evaluation_is_stable_and_not_blocked() -> None:
    candidate = CandidateInput(
        external_id="fixture-1",
        title="Tema local",
        summary="Resumen reproducible",
        canonical_url="https://example.test/topic",
    )
    evaluator = DeterministicCandidateEvaluator()

    first = evaluator.evaluate(candidate)
    second = evaluator.evaluate(candidate)

    assert first == second
    assert first.total_score > 0
    assert not first.is_blocked
