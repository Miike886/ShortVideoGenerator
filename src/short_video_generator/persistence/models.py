import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from short_video_generator.domain.enums import (
    ArtifactType,
    CandidateStatus,
    ProductionStatus,
    ReviewDecision,
    RunStatus,
    RunTrigger,
    StepStatus,
)


def new_id() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )


class NicheRecord(TimestampMixin, Base):
    __tablename__ = "niches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(20), default="es")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    schedule_interval_minutes: Mapped[int] = mapped_column(Integer, default=1440)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    editorial_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    selection_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    sources: Mapped[list["SourceConfigRecord"]] = relationship(
        back_populates="niche", cascade="all, delete-orphan"
    )
    runs: Mapped[list["PipelineRunRecord"]] = relationship(back_populates="niche")


class SourceConfigRecord(TimestampMixin, Base):
    __tablename__ = "source_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    niche_id: Mapped[str] = mapped_column(ForeignKey("niches.id"), index=True)
    type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    niche: Mapped[NicheRecord] = relationship(back_populates="sources")


class PipelineRunRecord(TimestampMixin, Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    niche_id: Mapped[str] = mapped_column(ForeignKey("niches.id"), index=True)
    trigger: Mapped[RunTrigger] = mapped_column(String(20))
    status: Mapped[RunStatus] = mapped_column(String(20), default=RunStatus.QUEUED, index=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    stats: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    niche: Mapped[NicheRecord] = relationship(back_populates="runs")
    candidates: Mapped[list["TopicCandidateRecord"]] = relationship(back_populates="run")
    productions: Mapped[list["ProductionRecord"]] = relationship(back_populates="run")
    steps: Mapped[list["StepRunRecord"]] = relationship(back_populates="run")


class TopicCandidateRecord(TimestampMixin, Base):
    __tablename__ = "topic_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    pipeline_run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)
    source_config_id: Mapped[str] = mapped_column(ForeignKey("source_configs.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(200))
    canonical_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    relevance_score: Mapped[float | None] = mapped_column(Float)
    novelty_score: Mapped[float | None] = mapped_column(Float)
    risk_score: Mapped[float | None] = mapped_column(Float)
    total_score: Mapped[float | None] = mapped_column(Float)
    evaluation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[CandidateStatus] = mapped_column(
        String(20), default=CandidateStatus.DISCOVERED
    )

    run: Mapped[PipelineRunRecord] = relationship(back_populates="candidates")


class ProductionRecord(TimestampMixin, Base):
    __tablename__ = "productions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    pipeline_run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)
    topic_candidate_id: Mapped[str] = mapped_column(
        ForeignKey("topic_candidates.id"), unique=True, index=True
    )
    status: Mapped[ProductionStatus] = mapped_column(
        String(30), default=ProductionStatus.SELECTED, index=True
    )
    current_step: Mapped[str | None] = mapped_column(String(50))
    failure_code: Mapped[str | None] = mapped_column(String(100))
    failure_message: Mapped[str | None] = mapped_column(Text)
    brief: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    script: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    validation_report: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    run: Mapped[PipelineRunRecord] = relationship(back_populates="productions")
    artifacts: Mapped[list["ArtifactRecord"]] = relationship(back_populates="production")
    reviews: Mapped[list["ReviewRecord"]] = relationship(back_populates="production")


class StepRunRecord(Base):
    __tablename__ = "step_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    pipeline_run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)
    production_id: Mapped[str | None] = mapped_column(ForeignKey("productions.id"), index=True)
    step: Mapped[str] = mapped_column(String(50))
    status: Mapped[StepStatus] = mapped_column(String(20), default=StepStatus.QUEUED)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)

    run: Mapped[PipelineRunRecord] = relationship(back_populates="steps")


class ArtifactRecord(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    production_id: Mapped[str] = mapped_column(ForeignKey("productions.id"), index=True)
    type: Mapped[ArtifactType] = mapped_column(String(30))
    relative_path: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    artifact_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    production: Mapped[ProductionRecord] = relationship(back_populates="artifacts")


class ReviewRecord(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    production_id: Mapped[str] = mapped_column(ForeignKey("productions.id"), index=True)
    decision: Mapped[ReviewDecision] = mapped_column(String(30))
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    production: Mapped[ProductionRecord] = relationship(back_populates="reviews")

