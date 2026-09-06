from dataclasses import dataclass

from sqlalchemy.engine import Engine

from short_video_generator.config import Settings
from short_video_generator.contracts import CandidateInput
from short_video_generator.persistence.database import build_engine, create_schema, session_factory
from short_video_generator.persistence.repositories import (
    SqlAlchemyExecutionRepository,
    SqlAlchemyReviewRepository,
)
from short_video_generator.pipeline.orchestrator import ManualPipeline
from short_video_generator.pipeline.review import ReviewService
from short_video_generator.providers.deterministic import (
    DeterministicEditorialProvider,
    DeterministicMediaProvider,
    DeterministicSpeechProvider,
    FixtureSourceProvider,
)
from short_video_generator.providers.evaluation import DeterministicCandidateEvaluator
from short_video_generator.rendering import FfmpegRenderer, FfprobeValidator
from short_video_generator.rendering.subtitles import BasicSubtitleProvider
from short_video_generator.storage import LocalArtifactStore


@dataclass(frozen=True, slots=True)
class ApiResources:
    review_service: ReviewService
    engine: Engine

    def close(self) -> None:
        self.engine.dispose()


def build_api_resources(settings: Settings) -> ApiResources:
    engine = build_engine(settings)
    create_schema(engine)
    sessions = session_factory(engine)
    return ApiResources(
        review_service=ReviewService(SqlAlchemyReviewRepository(sessions)),
        engine=engine,
    )


def build_manual_pipeline(settings: Settings) -> ManualPipeline:
    if settings.ffmpeg_path is None:
        raise RuntimeError("FFmpeg not found; set SVG_FFMPEG_PATH or add ffmpeg to PATH")
    if settings.ffprobe_path is None:
        raise RuntimeError("ffprobe not found; set SVG_FFPROBE_PATH or add ffprobe to PATH")
    engine = build_engine(settings)
    create_schema(engine)
    sessions = session_factory(engine)
    candidate = CandidateInput(
        external_id="fixture-candidate-1",
        title="Cómo funciona un pipeline de video local",
        summary=(
            "Un pipeline modular separa descubrimiento, decisiones editoriales, generación "
            "de recursos, renderizado y revisión humana."
        ),
        canonical_url="https://example.test/fixture/local-video-pipeline",
        source_payload={"fixture": True},
    )
    return ManualPipeline(
        repository=SqlAlchemyExecutionRepository(sessions),
        store=LocalArtifactStore(settings.storage_root),
        source=FixtureSourceProvider([candidate]),
        evaluator=DeterministicCandidateEvaluator(),
        editorial=DeterministicEditorialProvider(),
        speech=DeterministicSpeechProvider(),
        media=DeterministicMediaProvider(),
        subtitles=BasicSubtitleProvider(),
        renderer=FfmpegRenderer(settings.ffmpeg_path, settings.storage_root),
        validator=FfprobeValidator(settings.ffprobe_path),
    )
