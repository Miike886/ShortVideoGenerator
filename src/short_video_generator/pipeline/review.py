from short_video_generator.domain.enums import ProductionStatus, ReviewDecision
from short_video_generator.domain.transitions import require_transition, review_target
from short_video_generator.pipeline.models import ReviewItem, ReviewOutcome
from short_video_generator.pipeline.ports import ReviewRepository


class ReviewService:
    def __init__(self, repository: ReviewRepository) -> None:
        self.repository = repository

    def list_queue(self) -> list[ReviewItem]:
        return self.repository.list_by_status(ProductionStatus.AWAITING_REVIEW)

    def get(self, production_id: str) -> ReviewItem | None:
        return self.repository.get(production_id)

    def submit(self, production_id: str, decision: ReviewDecision, comment: str) -> ReviewOutcome:
        production = self.repository.get(production_id)
        if production is None:
            raise LookupError(production_id)
        target = review_target(decision)
        require_transition(production.status, target)
        return self.repository.save_decision(production_id, decision, comment, target)
