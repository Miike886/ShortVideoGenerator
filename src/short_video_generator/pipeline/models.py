import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from short_video_generator.domain.enums import (
    ArtifactType,
    CandidateStatus,
    ProductionStatus,
    ReviewDecision,
    RunStatus,
    RunTrigger,
    StepStatus,
)
from short_video_generator.pipeline.definitions import PipelineStep


def new_id() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class CandidateState:
    id: str = field(default_factory=new_id)
    external_id: str = ""
    canonical_url: str = ""
    title: str = ""
    summary: str = ""
    published_at: datetime | None = None
    raw_payload: dict[str, object] = field(default_factory=dict)
    fingerprint: str = ""
    status: CandidateStatus = CandidateStatus.DISCOVERED
    relevance_score: float | None = None
    novelty_score: float | None = None
    risk_score: float | None = None
    total_score: float | None = None
    evaluation: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ProductionState:
    id: str = field(default_factory=new_id)
    topic_candidate_id: str = ""
    status: ProductionStatus = ProductionStatus.SELECTED
    current_step: PipelineStep | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    brief: dict[str, object] | None = None
    script: dict[str, object] | None = None
    validation_report: dict[str, object] | None = None
    created_at: datetime = field(default_factory=now_utc)


@dataclass(slots=True)
class StepState:
    id: str = field(default_factory=new_id)
    step: PipelineStep = PipelineStep.DISCOVER
    production_id: str | None = None
    status: StepStatus = StepStatus.QUEUED
    attempt: int = 1
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    input_summary: dict[str, object] = field(default_factory=dict)
    output_summary: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ArtifactState:
    id: str = field(default_factory=new_id)
    artifact_type: ArtifactType = ArtifactType.IMAGE
    relative_path: Path = Path()
    mime_type: str = "application/octet-stream"
    size_bytes: int = 0
    sha256: str = ""
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=now_utc)


@dataclass(slots=True)
class ExecutionState:
    run_id: str = field(default_factory=new_id)
    niche_id: str = ""
    source_config_id: str = ""
    idempotency_key: str = ""
    trigger: RunTrigger = RunTrigger.MANUAL
    status: RunStatus = RunStatus.QUEUED
    scheduled_for: datetime = field(default_factory=now_utc)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    stats: dict[str, object] = field(default_factory=dict)
    candidate: CandidateState | None = None
    production: ProductionState | None = None
    steps: list[StepState] = field(default_factory=list)
    artifacts: list[ArtifactState] = field(default_factory=list)

    def step(self, name: PipelineStep, production_id: str | None) -> StepState | None:
        return next(
            (
                item
                for item in self.steps
                if item.step == name and item.production_id == production_id
            ),
            None,
        )


@dataclass(frozen=True, slots=True)
class StoredFile:
    relative_path: Path
    absolute_path: Path
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ReviewArtifact:
    artifact_type: ArtifactType
    relative_path: Path
    mime_type: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ReviewItem:
    id: str
    status: ProductionStatus
    title: str
    brief: dict[str, object]
    script: dict[str, object]
    validation_report: dict[str, object]
    artifacts: tuple[ReviewArtifact, ...]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ReviewOutcome:
    production_id: str
    status: ProductionStatus
    decision: ReviewDecision
    comment: str
    created_at: datetime
