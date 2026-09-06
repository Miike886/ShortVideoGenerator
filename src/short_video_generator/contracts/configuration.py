from pydantic import Field

from .common import Contract


class NicheDefinition(Contract):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2_000)
    language: str = Field(default="es", min_length=2, max_length=20)
    schedule_interval_minutes: int = Field(default=1440, ge=5)
    enabled: bool = True


class FixtureSourceDefinition(Contract):
    name: str = Field(default="fixture", min_length=1, max_length=200)
    enabled: bool = True

