from pydantic import Field

from .common import Contract


class CandidateEvaluation(Contract):
    relevance_score: float = Field(ge=0, le=100)
    novelty_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    total_score: float = Field(ge=0, le=100)
    rationale: tuple[str, ...] = Field(min_length=1)
    blocking_flags: tuple[str, ...] = ()

    @property
    def is_blocked(self) -> bool:
        return bool(self.blocking_flags)
