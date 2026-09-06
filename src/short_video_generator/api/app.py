from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from short_video_generator.api.schemas import ArtifactView, ReviewQueueItem, ReviewResult
from short_video_generator.bootstrap import build_api_resources
from short_video_generator.config import Settings
from short_video_generator.contracts import ReviewSubmission
from short_video_generator.domain.errors import InvalidStateTransition
from short_video_generator.pipeline.models import ReviewItem, ReviewOutcome


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.local()
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    resources = build_api_resources(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        resources.close()

    app = FastAPI(title="Short Video Generator", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.mount("/files", StaticFiles(directory=settings.storage_root), name="files")

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/review-queue", response_model=list[ReviewQueueItem], tags=["review"])
    def review_queue() -> list[ReviewQueueItem]:
        return [_queue_view(item) for item in resources.review_service.list_queue()]

    @app.get("/productions/{production_id}", response_model=ReviewQueueItem, tags=["review"])
    def production_detail(production_id: str) -> ReviewQueueItem:
        production = resources.review_service.get(production_id)
        if production is None:
            raise HTTPException(status_code=404, detail="Production not found")
        return _queue_view(production)

    @app.post("/productions/{production_id}/reviews", response_model=ReviewResult, tags=["review"])
    def submit_review(production_id: str, submission: ReviewSubmission) -> ReviewResult:
        try:
            outcome = resources.review_service.submit(
                production_id, submission.decision, submission.comment
            )
        except LookupError as error:
            raise HTTPException(status_code=404, detail="Production not found") from error
        except InvalidStateTransition as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return _result_view(outcome)

    return app


def _queue_view(item: ReviewItem) -> ReviewQueueItem:
    return ReviewQueueItem(
        id=item.id,
        status=item.status,
        title=item.title,
        brief=item.brief,
        script=item.script,
        validation_report=item.validation_report,
        artifacts=tuple(
            ArtifactView(
                type=artifact.artifact_type,
                relative_path=artifact.relative_path.as_posix(),
                mime_type=artifact.mime_type,
                size_bytes=artifact.size_bytes,
                sha256=artifact.sha256,
                url=f"/files/{artifact.relative_path.as_posix()}",
            )
            for artifact in item.artifacts
        ),
        created_at=item.created_at,
    )


def _result_view(outcome: ReviewOutcome) -> ReviewResult:
    return ReviewResult(
        production_id=outcome.production_id,
        status=outcome.status,
        decision=outcome.decision,
        comment=outcome.comment,
        created_at=outcome.created_at,
    )
