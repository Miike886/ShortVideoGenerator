from itertools import pairwise

import pytest

from short_video_generator.domain.enums import ProductionStatus, ReviewDecision
from short_video_generator.domain.errors import InvalidStateTransition
from short_video_generator.domain.transitions import require_transition, review_target


def test_happy_path_reaches_review_queue() -> None:
    path = (
        ProductionStatus.SELECTED,
        ProductionStatus.BRIEF_READY,
        ProductionStatus.SCRIPT_READY,
        ProductionStatus.ASSETS_READY,
        ProductionStatus.RENDERED,
        ProductionStatus.VALIDATING,
        ProductionStatus.AWAITING_REVIEW,
    )
    for current, target in pairwise(path):
        require_transition(current, target)


def test_cannot_approve_before_human_review_queue() -> None:
    with pytest.raises(InvalidStateTransition):
        require_transition(ProductionStatus.RENDERED, ProductionStatus.APPROVED)


@pytest.mark.parametrize("decision", list(ReviewDecision))
def test_review_decisions_map_to_terminal_or_revision_states(decision: ReviewDecision) -> None:
    target = review_target(decision)
    require_transition(ProductionStatus.AWAITING_REVIEW, target)
