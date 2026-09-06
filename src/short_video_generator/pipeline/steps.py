from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

from short_video_generator.domain.enums import StepStatus
from short_video_generator.pipeline.definitions import PipelineStep
from short_video_generator.pipeline.models import ExecutionState, StepState
from short_video_generator.pipeline.ports import ExecutionRepository

T = TypeVar("T")


class StepExecutor:
    def __init__(self, repository: ExecutionRepository) -> None:
        self.repository = repository

    def completed(
        self, execution: ExecutionState, step: PipelineStep, production_id: str | None
    ) -> bool:
        record = execution.step(step, production_id)
        return bool(record and record.status == StepStatus.COMPLETED)

    def run(
        self,
        execution: ExecutionState,
        step: PipelineStep,
        production_id: str | None,
        action: Callable[[], T],
    ) -> T:
        record = execution.step(step, production_id)
        if record and record.status == StepStatus.COMPLETED:
            raise RuntimeError(f"Completed step {step} must be handled by its caller")
        if record is None:
            record = StepState(step=step, production_id=production_id)
            execution.steps.append(record)
        else:
            record.attempt += 1
        record.status = StepStatus.RUNNING
        record.started_at = datetime.now(UTC)
        record.finished_at = None
        record.error_message = None
        self.repository.save(execution)
        try:
            result = action()
            record.status = StepStatus.COMPLETED
            record.finished_at = datetime.now(UTC)
            self.repository.save(execution)
            return result
        except Exception as error:
            persisted = self.repository.load(execution.idempotency_key)
            if persisted is not None:
                failed = persisted.step(step, production_id)
                if failed is not None:
                    failed.status = StepStatus.FAILED
                    failed.finished_at = datetime.now(UTC)
                    failed.error_message = str(error)
                    self.repository.save(persisted)
            raise
