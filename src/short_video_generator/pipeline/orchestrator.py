import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from short_video_generator.contracts import (
    CandidateInput,
    EditorialBrief,
    GeneratedAsset,
    RenderRequest,
    VideoScript,
)
from short_video_generator.domain.enums import (
    ArtifactType,
    CandidateStatus,
    ProductionStatus,
    RunStatus,
)
from short_video_generator.domain.transitions import require_transition
from short_video_generator.pipeline.definitions import PipelineStep
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
    SubtitleProvider,
)
from short_video_generator.pipeline.steps import StepExecutor
from short_video_generator.providers.ports import (
    CandidateEvaluator,
    EditorialProvider,
    MediaProvider,
    Renderer,
    SourceProvider,
    SpeechProvider,
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
        speech: SpeechProvider,
        media: MediaProvider,
        subtitles: SubtitleProvider,
        renderer: Renderer,
        validator: MediaValidator,
    ) -> None:
        self.repository = repository
        self.store = store
        self.source = source
        self.evaluator = evaluator
        self.editorial = editorial
        self.speech = speech
        self.media = media
        self.subtitles = subtitles
        self.renderer = renderer
        self.validator = validator
        self.steps = StepExecutor(repository)

    def execute(self, idempotency_key: str = "manual-fixture-v1") -> PipelineResult:
        execution = self.repository.load(idempotency_key)
        if execution and execution.status == RunStatus.COMPLETED:
            production = self._required_production(execution)
            return self._result(execution, production, reused=True)

        execution = execution or self.repository.create(idempotency_key)
        execution.status = RunStatus.RUNNING
        execution.started_at = execution.started_at or datetime.now(UTC)
        execution.error_message = None
        self.repository.save(execution)
        work = self.store.prepare_work_directory(execution.run_id)

        try:
            candidate = self._discover(execution)
            self._evaluate(execution, candidate)
            production = self._select(execution, candidate)
            self._create_brief(execution, candidate, production)
            self._create_script(execution, production)
            self._generate_assets(execution, production, work)
            render_path = self._render(execution, production, work)
            self._validate(execution, production, render_path, work)
            self._enqueue_review(execution, production)
            execution.status = RunStatus.COMPLETED
            execution.finished_at = datetime.now(UTC)
            execution.stats = {"candidates": 1, "productions": 1}
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
            if not 3 <= len(script.scenes) <= 5:
                raise ValueError("Script must contain between 3 and 5 scenes")
            self._transition(production, ProductionStatus.SCRIPT_READY, PipelineStep.CREATE_SCRIPT)
            production.script = script.model_dump(mode="json")

        self.steps.run(execution, PipelineStep.CREATE_SCRIPT, production.id, action)

    def _generate_assets(
        self, execution: ExecutionState, production: ProductionState, work: Path
    ) -> None:
        if self.steps.completed(execution, PipelineStep.GENERATE_ASSETS, production.id):
            return

        def action() -> None:
            script = VideoScript.model_validate(production.script)
            drafts = self.media.create_visuals(script, work)
            narration = " ".join(scene.narration for scene in script.scenes)
            drafts.append(self.speech.synthesize(narration, work))
            drafts.append(self.subtitles.create(script, work))
            final_directory = self.store.asset_directory(production.id)
            for draft in drafts:
                stored = self.store.promote(
                    work / draft.relative_path,
                    final_directory / draft.relative_path.name,
                )
                self._upsert_artifact(
                    execution,
                    draft.artifact_type,
                    draft.media_type,
                    draft.metadata,
                    stored,
                )
            self._transition(
                production, ProductionStatus.ASSETS_READY, PipelineStep.GENERATE_ASSETS
            )

        self.steps.run(execution, PipelineStep.GENERATE_ASSETS, production.id, action)

    def _render(self, execution: ExecutionState, production: ProductionState, work: Path) -> Path:
        render = self._artifact(execution, ArtifactType.RENDER)
        if render is not None:
            return self.store.resolve(render.relative_path)

        def action() -> Path:
            result = self.renderer.render(
                RenderRequest(
                    production_id=production.id,
                    script=VideoScript.model_validate(production.script),
                    assets=tuple(self._artifact_contracts(execution)),
                ),
                work,
            )
            stored = self.store.promote(
                work / result.render.relative_path,
                self.store.render_directory(production.id) / "final.mp4",
            )
            self._upsert_artifact(
                execution,
                ArtifactType.RENDER,
                "video/mp4",
                result.render.metadata,
                stored,
            )
            self._transition(production, ProductionStatus.RENDERED, PipelineStep.RENDER)
            return stored.absolute_path

        return self.steps.run(execution, PipelineStep.RENDER, production.id, action)

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
            report = self.validator.validate(render_path)
            production.validation_report = report.model_dump(mode="json")
            report_path = self.store.write_text(
                work, "validation.json", report.model_dump_json(indent=2)
            )
            stored = self.store.promote(
                report_path,
                self.store.asset_directory(production.id) / report_path.name,
            )
            self._upsert_artifact(
                execution,
                ArtifactType.VALIDATION_REPORT,
                "application/json",
                {"passed": report.passed},
                stored,
            )
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
    def _artifact(execution: ExecutionState, artifact_type: ArtifactType) -> ArtifactState | None:
        return next(
            (item for item in execution.artifacts if item.artifact_type == artifact_type),
            None,
        )

    @staticmethod
    def _artifact_contracts(execution: ExecutionState) -> list[GeneratedAsset]:
        return [
            GeneratedAsset(
                artifact_type=item.artifact_type,
                relative_path=item.relative_path,
                media_type=item.mime_type,
                metadata=item.metadata,
            )
            for item in execution.artifacts
        ]

    @staticmethod
    def _upsert_artifact(
        execution: ExecutionState,
        artifact_type: ArtifactType,
        media_type: str,
        metadata: dict[str, object],
        stored: StoredFile,
    ) -> None:
        existing = next(
            (item for item in execution.artifacts if item.relative_path == stored.relative_path),
            None,
        )
        if existing is None:
            execution.artifacts.append(
                ArtifactState(
                    artifact_type=artifact_type,
                    relative_path=stored.relative_path,
                    mime_type=media_type,
                    size_bytes=stored.size_bytes,
                    sha256=stored.sha256,
                    metadata=metadata,
                )
            )
            return
        existing.artifact_type = artifact_type
        existing.mime_type = media_type
        existing.size_bytes = stored.size_bytes
        existing.sha256 = stored.sha256
        existing.metadata = metadata
