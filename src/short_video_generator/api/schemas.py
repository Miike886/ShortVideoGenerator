from datetime import datetime

from pydantic import BaseModel, ConfigDict

from short_video_generator.domain.enums import ArtifactType, ProductionStatus, ReviewDecision


class ArtifactView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: ArtifactType
    relative_path: str
    mime_type: str
    size_bytes: int
    sha256: str
    url: str


class ReviewQueueItem(BaseModel):
    id: str
    status: ProductionStatus
    title: str
    brief: dict[str, object]
    script: dict[str, object]
    validation_report: dict[str, object]
    artifacts: tuple[ArtifactView, ...]
    created_at: datetime


class ReviewResult(BaseModel):
    production_id: str
    status: ProductionStatus
    decision: ReviewDecision
    comment: str
    created_at: datetime
