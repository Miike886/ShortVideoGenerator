from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

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
from short_video_generator.pipeline.models import (
    ArtifactState,
    CandidateState,
    ExecutionState,
    ProductionState,
    ReviewArtifact,
    ReviewItem,
    ReviewOutcome,
    StepState,
)

from .models import (
    ArtifactRecord,
    NicheRecord,
    PipelineRunRecord,
    ProductionRecord,
    ReviewRecord,
    SourceConfigRecord,
    StepRunRecord,
    TopicCandidateRecord,
)


class SqlAlchemyExecutionRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    def load(self, idempotency_key: str) -> ExecutionState | None:
        with self.sessions() as session:
            run = session.scalar(
                select(PipelineRunRecord).where(
                    PipelineRunRecord.idempotency_key == idempotency_key
                )
            )
            return None if run is None else self._to_state(session, run)

    def create(self, idempotency_key: str) -> ExecutionState:
        with self.sessions() as session:
            niche = session.scalar(select(NicheRecord).where(NicheRecord.name == "fixture-niche"))
            if niche is None:
                niche = NicheRecord(
                    name="fixture-niche",
                    description="Deterministic local MVP niche",
                    language="es",
                    enabled=True,
                )
                session.add(niche)
                session.flush()
            source = session.scalar(
                select(SourceConfigRecord).where(
                    SourceConfigRecord.niche_id == niche.id,
                    SourceConfigRecord.name == "fixture-source",
                )
            )
            if source is None:
                source = SourceConfigRecord(
                    niche_id=niche.id,
                    type="fixture",
                    name="fixture-source",
                    enabled=True,
                    config={"candidate_count": 1},
                )
                session.add(source)
                session.flush()
            state = ExecutionState(
                niche_id=niche.id,
                source_config_id=source.id,
                idempotency_key=idempotency_key,
            )
            session.add(self._new_run(state))
            session.commit()
            return state

    def save(self, execution: ExecutionState) -> None:
        with self.sessions() as session:
            run = session.get(PipelineRunRecord, execution.run_id)
            if run is None:
                run = self._new_run(execution)
                session.add(run)
            self._copy_run(execution, run)
            if execution.candidate is not None:
                candidate = session.get(TopicCandidateRecord, execution.candidate.id)
                if candidate is None:
                    candidate = TopicCandidateRecord(
                        id=execution.candidate.id,
                        pipeline_run_id=execution.run_id,
                        source_config_id=execution.source_config_id,
                        external_id=execution.candidate.external_id,
                        canonical_url=execution.candidate.canonical_url,
                        title=execution.candidate.title,
                        summary=execution.candidate.summary,
                        fingerprint=execution.candidate.fingerprint,
                    )
                    session.add(candidate)
                self._copy_candidate(execution.candidate, candidate)
            if execution.production is not None:
                production = session.get(ProductionRecord, execution.production.id)
                if production is None:
                    production = ProductionRecord(
                        id=execution.production.id,
                        pipeline_run_id=execution.run_id,
                        topic_candidate_id=execution.production.topic_candidate_id,
                    )
                    session.add(production)
                self._copy_production(execution.production, production)
            for state in execution.steps:
                record = session.get(StepRunRecord, state.id)
                if record is None:
                    record = StepRunRecord(
                        id=state.id,
                        pipeline_run_id=execution.run_id,
                        production_id=state.production_id,
                        step=state.step,
                    )
                    session.add(record)
                self._copy_step(state, record)
            if execution.production is not None:
                for state in execution.artifacts:
                    record = session.get(ArtifactRecord, state.id)
                    if record is None:
                        record = ArtifactRecord(
                            id=state.id,
                            production_id=execution.production.id,
                            type=state.artifact_type,
                            relative_path=state.relative_path.as_posix(),
                            mime_type=state.mime_type,
                            size_bytes=state.size_bytes,
                            sha256=state.sha256,
                        )
                        session.add(record)
                    self._copy_artifact(state, record)
            session.commit()

    @staticmethod
    def _new_run(state: ExecutionState) -> PipelineRunRecord:
        return PipelineRunRecord(
            id=state.run_id,
            niche_id=state.niche_id,
            idempotency_key=state.idempotency_key,
            trigger=state.trigger,
            status=state.status,
            scheduled_for=state.scheduled_for,
        )

    @staticmethod
    def _copy_run(state: ExecutionState, record: PipelineRunRecord) -> None:
        record.trigger = state.trigger
        record.status = state.status
        record.scheduled_for = state.scheduled_for
        record.started_at = state.started_at
        record.finished_at = state.finished_at
        record.error_message = state.error_message
        record.stats = state.stats

    @staticmethod
    def _copy_candidate(state: CandidateState, record: TopicCandidateRecord) -> None:
        record.canonical_url = state.canonical_url
        record.title = state.title
        record.summary = state.summary
        record.published_at = state.published_at
        record.raw_payload = state.raw_payload
        record.fingerprint = state.fingerprint
        record.relevance_score = state.relevance_score
        record.novelty_score = state.novelty_score
        record.risk_score = state.risk_score
        record.total_score = state.total_score
        record.evaluation = state.evaluation
        record.status = state.status

    @staticmethod
    def _copy_production(state: ProductionState, record: ProductionRecord) -> None:
        record.status = state.status
        record.current_step = state.current_step
        record.failure_code = state.failure_code
        record.failure_message = state.failure_message
        record.brief = state.brief
        record.script = state.script
        record.validation_report = state.validation_report

    @staticmethod
    def _copy_step(state: StepState, record: StepRunRecord) -> None:
        record.status = state.status
        record.attempt = state.attempt
        record.started_at = state.started_at
        record.finished_at = state.finished_at
        record.error_message = state.error_message
        record.input_summary = state.input_summary
        record.output_summary = state.output_summary

    @staticmethod
    def _copy_artifact(state: ArtifactState, record: ArtifactRecord) -> None:
        record.type = state.artifact_type
        record.relative_path = state.relative_path.as_posix()
        record.mime_type = state.mime_type
        record.size_bytes = state.size_bytes
        record.sha256 = state.sha256
        record.artifact_metadata = state.metadata

    @staticmethod
    def _to_state(session: Session, run: PipelineRunRecord) -> ExecutionState:
        candidate_record = session.scalar(
            select(TopicCandidateRecord).where(TopicCandidateRecord.pipeline_run_id == run.id)
        )
        production_record = session.scalar(
            select(ProductionRecord).where(ProductionRecord.pipeline_run_id == run.id)
        )
        candidate = (
            None
            if candidate_record is None
            else CandidateState(
                id=candidate_record.id,
                external_id=candidate_record.external_id,
                canonical_url=candidate_record.canonical_url,
                title=candidate_record.title,
                summary=candidate_record.summary,
                published_at=candidate_record.published_at,
                raw_payload=candidate_record.raw_payload,
                fingerprint=candidate_record.fingerprint,
                status=CandidateStatus(candidate_record.status),
                relevance_score=candidate_record.relevance_score,
                novelty_score=candidate_record.novelty_score,
                risk_score=candidate_record.risk_score,
                total_score=candidate_record.total_score,
                evaluation=candidate_record.evaluation,
            )
        )
        production = (
            None
            if production_record is None
            else ProductionState(
                id=production_record.id,
                topic_candidate_id=production_record.topic_candidate_id,
                status=ProductionStatus(production_record.status),
                current_step=(
                    PipelineStep(production_record.current_step)
                    if production_record.current_step
                    else None
                ),
                failure_code=production_record.failure_code,
                failure_message=production_record.failure_message,
                brief=production_record.brief,
                script=production_record.script,
                validation_report=production_record.validation_report,
                created_at=production_record.created_at,
            )
        )
        steps = [
            StepState(
                id=record.id,
                step=PipelineStep(record.step),
                production_id=record.production_id,
                status=StepStatus(record.status),
                attempt=record.attempt,
                started_at=record.started_at,
                finished_at=record.finished_at,
                error_message=record.error_message,
                input_summary=record.input_summary,
                output_summary=record.output_summary,
            )
            for record in session.scalars(
                select(StepRunRecord).where(StepRunRecord.pipeline_run_id == run.id)
            )
        ]
        artifacts = []
        if production_record is not None:
            artifacts = [
                ArtifactState(
                    id=record.id,
                    artifact_type=ArtifactType(record.type),
                    relative_path=Path(record.relative_path),
                    mime_type=record.mime_type,
                    size_bytes=record.size_bytes,
                    sha256=record.sha256,
                    metadata=record.artifact_metadata,
                    created_at=record.created_at,
                )
                for record in session.scalars(
                    select(ArtifactRecord).where(
                        ArtifactRecord.production_id == production_record.id
                    )
                )
            ]
        source = session.scalar(
            select(SourceConfigRecord).where(SourceConfigRecord.niche_id == run.niche_id)
        )
        if source is None:
            raise RuntimeError(f"Source configuration missing for run {run.id}")
        return ExecutionState(
            run_id=run.id,
            niche_id=run.niche_id,
            source_config_id=source.id,
            idempotency_key=run.idempotency_key,
            trigger=RunTrigger(run.trigger),
            status=RunStatus(run.status),
            scheduled_for=run.scheduled_for,
            started_at=run.started_at,
            finished_at=run.finished_at,
            error_message=run.error_message,
            stats=run.stats,
            candidate=candidate,
            production=production,
            steps=steps,
            artifacts=artifacts,
        )


class SqlAlchemyReviewRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    def list_by_status(self, status: ProductionStatus) -> list[ReviewItem]:
        with self.sessions() as session:
            records = session.scalars(
                select(ProductionRecord)
                .where(ProductionRecord.status == status)
                .order_by(ProductionRecord.created_at)
            ).all()
            return [self._review_item(session, record) for record in records]

    def get(self, production_id: str) -> ReviewItem | None:
        with self.sessions() as session:
            record = session.get(ProductionRecord, production_id)
            return None if record is None else self._review_item(session, record)

    def save_decision(
        self,
        production_id: str,
        decision: ReviewDecision,
        comment: str,
        target: ProductionStatus,
    ) -> ReviewOutcome:
        with self.sessions() as session:
            production = session.get(ProductionRecord, production_id)
            if production is None:
                raise LookupError(production_id)
            production.status = target
            review = ReviewRecord(
                production_id=production_id,
                decision=decision,
                comment=comment,
            )
            session.add(review)
            session.commit()
            session.refresh(review)
            return ReviewOutcome(
                production_id=production_id,
                status=target,
                decision=decision,
                comment=comment,
                created_at=review.created_at,
            )

    @staticmethod
    def _review_item(session: Session, production: ProductionRecord) -> ReviewItem:
        candidate = session.get(TopicCandidateRecord, production.topic_candidate_id)
        if candidate is None:
            raise RuntimeError(f"Candidate missing for production {production.id}")
        artifacts = session.scalars(
            select(ArtifactRecord)
            .where(ArtifactRecord.production_id == production.id)
            .order_by(ArtifactRecord.created_at)
        ).all()
        return ReviewItem(
            id=production.id,
            status=ProductionStatus(production.status),
            title=candidate.title,
            brief=production.brief or {},
            script=production.script or {},
            validation_report=production.validation_report or {},
            artifacts=tuple(
                ReviewArtifact(
                    artifact_type=ArtifactType(item.type),
                    relative_path=Path(item.relative_path),
                    mime_type=item.mime_type,
                    size_bytes=item.size_bytes,
                    sha256=item.sha256,
                )
                for item in artifacts
            ),
            created_at=production.created_at,
        )
