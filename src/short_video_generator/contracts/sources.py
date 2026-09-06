from datetime import datetime

from pydantic import Field, HttpUrl

from .common import Contract


class CandidateInput(Contract):
    external_id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=300)
    summary: str = Field(min_length=1, max_length=5_000)
    canonical_url: HttpUrl
    published_at: datetime | None = None
    source_payload: dict[str, object] = Field(default_factory=dict)
