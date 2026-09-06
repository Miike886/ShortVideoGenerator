from collections.abc import Mapping

from .enums import ProductionStatus, ReviewDecision
from .errors import InvalidStateTransition


PRODUCTION_TRANSITIONS: Mapping[ProductionStatus, frozenset[ProductionStatus]] = {
    ProductionStatus.SELECTED: frozenset({ProductionStatus.BRIEF_READY, ProductionStatus.FAILED}),
    ProductionStatus.BRIEF_READY: frozenset(
        {ProductionStatus.SCRIPT_READY, ProductionStatus.FAILED}
    ),
    ProductionStatus.SCRIPT_READY: frozenset(
        {ProductionStatus.ASSETS_READY, ProductionStatus.FAILED}
    ),
    ProductionStatus.ASSETS_READY: frozenset(
        {ProductionStatus.RENDERED, ProductionStatus.FAILED}
    ),
    ProductionStatus.RENDERED: frozenset(
        {ProductionStatus.VALIDATING, ProductionStatus.FAILED}
    ),
    ProductionStatus.VALIDATING: frozenset(
        {
            ProductionStatus.AWAITING_REVIEW,
            ProductionStatus.VALIDATION_FAILED,
            ProductionStatus.FAILED,
        }
    ),
    ProductionStatus.VALIDATION_FAILED: frozenset(
        {ProductionStatus.ASSETS_READY, ProductionStatus.FAILED}
    ),
    ProductionStatus.AWAITING_REVIEW: frozenset(
        {
            ProductionStatus.APPROVED,
            ProductionStatus.REJECTED,
            ProductionStatus.CHANGES_REQUESTED,
        }
    ),
    ProductionStatus.CHANGES_REQUESTED: frozenset(
        {ProductionStatus.BRIEF_READY, ProductionStatus.SCRIPT_READY, ProductionStatus.FAILED}
    ),
    ProductionStatus.APPROVED: frozenset(),
    ProductionStatus.REJECTED: frozenset(),
    ProductionStatus.FAILED: frozenset(),
}


def require_transition(current: ProductionStatus, target: ProductionStatus) -> None:
    if target not in PRODUCTION_TRANSITIONS[current]:
        raise InvalidStateTransition(f"Cannot transition production from {current} to {target}")


def review_target(decision: ReviewDecision) -> ProductionStatus:
    return ProductionStatus(decision.value)

