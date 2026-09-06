import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from short_video_generator.contracts import CandidateInput, EditorialBrief, VideoScript
from short_video_generator.domain.enums import (
    ArtifactType,
    CandidateStatus,
    ProductionStatus,
    RunStatus,
)
from short_video_generator.domain.transitions import require_transition
from short_video_generator.pipeline.definitions import PipelineStep
from short_video_generator.pipeline.media_workflow import NarratedMediaWorkflow
from short_video_generator.pipeline.models import (
    ArtifactState,
    CandidateState,
    ExecutionState,
    ProductionState,
    StoredFile,
)
from short_video_generator.pipeline.ports import (
    ArtifactStore,
    ExecutionRepository,
    MediaValidator,
)
from short_video_generator.pipeline.steps import StepExecutor
from short_video_generator.providers.ports import (
    CandidateEvaluator,
    EditorialProvider,
    SourceProvider,
)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    run_id: str
    production_id: str
    status: ProductionStatus
    reused: bool


class ManualPipeline:
    def __init__(
        self,
        repository: ExecutionRepository,
        store: ArtifactStore,
        source: SourceProvider,
        evaluator: CandidateEvaluator,
        editorial: EditorialProvider,
        media_workflow: NarratedMediaWorkflow,
        validator: MediaValidator,
        input_fingerprint: str,
    ) -> None:
        self.repository = repository
        self.store = store
        self.source = source
        self.evaluator = evaluator
        self.editorial = editorial
        self.media_workflow = media_workflow
        self.validator = validator
        self.input_fingerprint = input_fingerprint
        self.steps = StepExecutor(repository)

    def execute(self, idempotency_key: str = "manual-fixture-v1") -> PipelineResult:
        execution = self.repository.load(idempotency_key)
        if (
            execution
            and execution.stats.get("input_fingerprint") != self.input_fingerprint
        ):
            raise ValueError(
                "Idempotency key is already associated with different production inputs"
            )
        if execution and execution.status == RunStatus.COMPLETED:
            for step in execution.steps:
                step.output_summary["reused"] = True
            self.repository.save(execution)
            production = self._required_production(execution)
            return self._result(execution, production, reused=True)

        execution = execution or self.repository.create(idempotency_key)
        execution.status = RunStatus.RUNNING
        execution.started_at = execution.started_at or datetime.now(UTC)
        execution.error_message = None
        execution.stats["input_fingerprint"] = self.input_fingerprint
        self.repository.save(execution)
        work = self.store.prepare_work_directory(execution.run_id)

        try:
            candidate = self._discover(execution)
            self._evaluate(execution, candidate)
            production = self._select(execution, candidate)
            self._create_brief(execution, candidate, production)
            self._create_script(execution, production)
            render_path = self.media_workflow.render(execution, production, work)
            self._validate(execution, production, render_path, work)
            self._enqueue_review(execution, production)
            execution.status = RunStatus.COMPLETED
            execution.finished_at = datetime.now(UTC)
            execution.stats |= {"candidates": 1, "productions": 1}
            self.repository.save(execution)
        except Exception as error:
            persisted = self.repository.load(idempotency_key)
            if persisted is not None:
                persisted.status = RunStatus.FAILED
                persisted.finished_at = datetime.now(UTC)
                persisted.error_message = str(error)
                self.repository.save(persisted)
            raise
        finally:
            self.store.cleanup_work_directory(execution.run_id)

        return self._result(execution, production, reused=False)

    def _discover(self, execution: ExecutionState) -> CandidateState:
        if execution.candidate is not None:
            return execution.candidate

        def action() -> CandidateState:
            inputs = self.source.fetch("fixture-niche")
            if len(inputs) != 1:
                raise ValueError("The fixture source must return exactly one candidate")
            item = inputs[0]
            candidate = CandidateState(
                external_id=item.external_id,
                canonical_url=str(item.canonical_url),
                title=item.title,
                summary=item.summary,
                published_at=item.published_at,
                raw_payload=item.source_payload,
                fingerprint=hashlib.sha256(
                    f"{item.external_id}|{item.title}|{item.canonical_url}".encode()
                ).hexdigest(),
            )
            execution.candidate = candidate
            return candidate

        return self.steps.run(execution, PipelineStep.DISCOVER, None, action)

    def _evaluate(self, execution: ExecutionState, candidate: CandidateState) -> None:
        if candidate.status != CandidateStatus.DISCOVERED:
            return

        def action() -> None:
            evaluation = self.evaluator.evaluate(self._candidate_contract(candidate))
            candidate.relevance_score = evaluation.relevance_score
            candidate.novelty_score = evaluation.novelty_score
            candidate.risk_score = evaluation.risk_score
            candidate.total_score = evaluation.total_score
            candidate.evaluation = evaluation.model_dump(mode="json")
            candidate.status = (
                CandidateStatus.BLOCKED if evaluation.is_blocked else CandidateStatus.EVALUATED
            )

        self.steps.run(execution, PipelineStep.EVALUATE, None, action)

    def _select(self, execution: ExecutionState, candidate: CandidateState) -> ProductionState:
        if execution.production is not None:
            return execution.production

        def action() -> ProductionState:
            if candidate.status != CandidateStatus.EVALUATED:
                raise ValueError("Candidate must be evaluated and unblocked before selection")
            candidate.status = CandidateStatus.SELECTED
            production = ProductionState(
                topic_candidate_id=candidate.id,
                current_step=PipelineStep.SELECT,
            )
            execution.production = production
            return production

        return self.steps.run(execution, PipelineStep.SELECT, None, action)

    def _create_brief(
        self,
        execution: ExecutionState,
        candidate: CandidateState,
        production: ProductionState,
    ) -> None:
        if production.brief is not None:
            return

        def action() -> None:
            brief = self.editorial.create_brief(self._candidate_contract(candidate))
            self._transition(production, ProductionStatus.BRIEF_READY, PipelineStep.CREATE_BRIEF)
            production.brief = brief.model_dump(mode="json")

        self.steps.run(execution, PipelineStep.CREATE_BRIEF, production.id, action)

    def _create_script(self, execution: ExecutionState, production: ProductionState) -> None:
        if production.script is not None:
            return

        def action() -> None:
            script = self.editorial.create_script(EditorialBrief.model_validate(production.brief))
            if len(script.scenes) != 3:
                raise ValueError("The narrated MVP script must contain exactly three scenes")
            self._transition(production, ProductionStatus.SCRIPT_READY, PipelineStep.CREATE_SCRIPT)
            production.script = script.model_dump(mode="json")

        self.steps.run(execution, PipelineStep.CREATE_SCRIPT, production.id, action)

    def _validate(
        self,
        execution: ExecutionState,
        production: ProductionState,
        render_path: Path,
        work: Path,
    ) -> None:
        if production.validation_report is not None:
            return

        def action() -> None:
            self._transition(production, ProductionStatus.VALIDATING, PipelineStep.VALIDATE)
            expected_duration = VideoScript.model_validate(production.script).duration_seconds
            report = self.validator.validate(render_path, expected_duration)
            production.validation_report = report.model_dump(mode="json")
            report_path = self.store.write_text(
                work, "validation.json", report.model_dump_json(indent=2)
            )
            stored = self.store.promote(
                report_path,
                self.store.asset_directory(production.id) / report_path.name,
            )
            self._upsert_validation_artifact(execution, report.passed, stored)
            if not report.passed:
                self._transition(
                    production,
                    ProductionStatus.VALIDATION_FAILED,
                    PipelineStep.VALIDATE,
                )
                raise ValueError("Rendered video did not pass technical validation")

        self.steps.run(execution, PipelineStep.VALIDATE, production.id, action)

    def _enqueue_review(self, execution: ExecutionState, production: ProductionState) -> None:
        if production.status == ProductionStatus.AWAITING_REVIEW:
            return

        def action() -> None:
            self._transition(
                production, ProductionStatus.AWAITING_REVIEW, PipelineStep.ENQUEUE_REVIEW
            )

        self.steps.run(execution, PipelineStep.ENQUEUE_REVIEW, production.id, action)

    @staticmethod
    def _transition(
        production: ProductionState, target: ProductionStatus, step: PipelineStep
    ) -> None:
        require_transition(production.status, target)
        production.status = target
        production.current_step = step

    @staticmethod
    def _candidate_contract(candidate: CandidateState) -> CandidateInput:
        return CandidateInput(
            external_id=candidate.external_id,
            title=candidate.title,
            summary=candidate.summary,
            canonical_url=candidate.canonical_url,
            published_at=candidate.published_at,
            source_payload=candidate.raw_payload,
        )

    @staticmethod
    def _required_production(execution: ExecutionState) -> ProductionState:
        if execution.production is None:
            raise LookupError(f"No production exists for completed run {execution.run_id}")
        return execution.production

    @staticmethod
    def _result(
        execution: ExecutionState, production: ProductionState, reused: bool
    ) -> PipelineResult:
        return PipelineResult(
            run_id=execution.run_id,
            production_id=production.id,
            status=production.status,
            reused=reused,
        )

    @staticmethod
    def _upsert_validation_artifact(
        execution: ExecutionState, passed: bool, stored: StoredFile
    ) -> None:
        existing = next(
            (item for item in execution.artifacts if item.relative_path == stored.relative_path),
            None,
        )
        if existing is None:
            execution.artifacts.append(
                ArtifactState(
                    artifact_type=ArtifactType.VALIDATION_REPORT,
                    relative_path=stored.relative_path,
                    mime_type="application/json",
                    size_bytes=stored.size_bytes,
                    sha256=stored.sha256,
                    metadata={"passed": passed},
                )
            )
            return
        existing.size_bytes = stored.size_bytes
        existing.sha256 = stored.sha256
        existing.metadata = {"passed": passed}
