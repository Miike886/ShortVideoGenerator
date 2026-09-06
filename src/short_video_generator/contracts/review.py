from pydantic import Field, model_validator

from short_video_generator.domain.enums import ReviewDecision

from .common import Contract


class ReviewSubmission(Contract):
    decision: ReviewDecision
    comment: str = Field(default="", max_length=2_000)

    @model_validator(mode="after")
    def feedback_is_required_when_not_approved(self) -> "ReviewSubmission":
        if self.decision != ReviewDecision.APPROVED and not self.comment.strip():
            raise ValueError("comment is required for rejection or requested changes")
        return self
