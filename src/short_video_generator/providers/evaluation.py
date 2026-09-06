from short_video_generator.contracts import CandidateEvaluation, CandidateInput


class DeterministicCandidateEvaluator:
    def evaluate(self, candidate: CandidateInput) -> CandidateEvaluation:
        title_signal = min(len(candidate.title) / 100, 1)
        summary_signal = min(len(candidate.summary) / 300, 1)
        relevance = round(70 + (title_signal * 10), 2)
        novelty = round(75 + (summary_signal * 10), 2)
        risk = 5.0
        total = round((relevance * 0.55) + (novelty * 0.35) - (risk * 0.10), 2)
        return CandidateEvaluation(
            relevance_score=relevance,
            novelty_score=novelty,
            risk_score=risk,
            total_score=total,
            rationale=("Deterministic length-based fixture scoring",),
        )
