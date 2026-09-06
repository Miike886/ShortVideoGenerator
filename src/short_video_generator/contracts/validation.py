from pydantic import Field, model_validator

from .common import Contract


class ValidationCheck(Contract):
    name: str = Field(min_length=1, max_length=100)
    passed: bool
    blocking: bool = True
    detail: str = Field(default="", max_length=1_000)


class ValidationReport(Contract):
    checks: tuple[ValidationCheck, ...] = Field(min_length=1)
    passed: bool

    @model_validator(mode="after")
    def result_matches_blocking_checks(self) -> "ValidationReport":
        expected = all(check.passed or not check.blocking for check in self.checks)
        if self.passed != expected:
            raise ValueError("passed must match the result of all blocking checks")
        return self
