class DomainError(Exception):
    """Base class for domain rule violations."""


class InvalidStateTransition(DomainError):
    pass
