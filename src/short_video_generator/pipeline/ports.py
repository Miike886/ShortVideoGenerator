from pathlib import Path
from typing import Protocol

from short_video_generator.contracts import (
    AudioProbeResult,
    LocalFileDraft,
    ValidationReport,
    VideoScript,
    WordTiming,
)
from short_video_generator.domain.enums import ProductionStatus, ReviewDecision
from short_video_generator.pipeline.models import (
    ExecutionState,
    ReviewItem,
    ReviewOutcome,
    StoredFile,
)


class ExecutionRepository(Protocol):
    def load(self, idempotency_key: str) -> ExecutionState | None: ...

    def create(self, idempotency_key: str) -> ExecutionState: ...

    def save(self, execution: ExecutionState) -> None: ...


class ArtifactStore(Protocol):
    root: Path

    def prepare_work_directory(self, run_id: str) -> Path: ...

    def asset_directory(self, production_id: str) -> Path: ...

    def render_directory(self, production_id: str) -> Path: ...

    def promote(self, source: Path, destination: Path) -> StoredFile: ...

    def resolve(self, relative_path: Path) -> Path: ...

    def write_text(self, directory: Path, filename: str, content: str) -> Path: ...

    def cleanup_work_directory(self, run_id: str) -> None: ...


class SubtitleProvider(Protocol):
    provider_name: str
    provider_version: str

    def create(
        self,
        script: VideoScript,
        words: tuple[WordTiming, ...],
        destination: Path,
    ) -> LocalFileDraft: ...


class MediaValidator(Protocol):
    def validate(
        self, render: Path, expected_duration_seconds: float | None = None
    ) -> ValidationReport: ...


class AudioProbe(Protocol):
    def inspect(self, audio: Path) -> AudioProbeResult: ...


class ReviewRepository(Protocol):
    def list_by_status(self, status: ProductionStatus) -> list[ReviewItem]: ...

    def get(self, production_id: str) -> ReviewItem | None: ...

    def save_decision(
        self,
        production_id: str,
        decision: ReviewDecision,
        comment: str,
        target: ProductionStatus,
    ) -> ReviewOutcome: ...
