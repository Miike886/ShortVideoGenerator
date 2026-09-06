import hashlib
import json
from dataclasses import dataclass

from sqlalchemy.engine import Engine

from short_video_generator.config import Settings
from short_video_generator.contracts import (
    CandidateInput,
    ManualProductionInput,
    TextToSpeechOptions,
)
from short_video_generator.persistence.database import build_engine, create_schema, session_factory
from short_video_generator.persistence.repositories import (
    SqlAlchemyExecutionRepository,
    SqlAlchemyReviewRepository,
)
from short_video_generator.pipeline.media_workflow import NarratedMediaWorkflow
from short_video_generator.pipeline.orchestrator import ManualPipeline
from short_video_generator.pipeline.review import ReviewService
from short_video_generator.pipeline.steps import StepExecutor
from short_video_generator.providers.assets import FakeAssetProvider, PexelsAssetProvider
from short_video_generator.providers.captions import (
    FakeCaptionAlignmentProvider,
    WhisperXCaptionAlignmentProvider,
)
from short_video_generator.providers.characters import LocalCharacterAssetProvider
from short_video_generator.providers.deterministic import (
    DeterministicEditorialProvider,
    FixtureSourceProvider,
)
from short_video_generator.providers.evaluation import DeterministicCandidateEvaluator
from short_video_generator.providers.ports import (
    AssetProvider,
    CaptionAlignmentProvider,
    CharacterAssetProvider,
    TextToSpeechProvider,
)
from short_video_generator.providers.tts import (
    EdgeTextToSpeechProvider,
    ElevenLabsTextToSpeechProvider,
    FakeTextToSpeechProvider,
)
from short_video_generator.rendering import (
    FfmpegRenderer,
    FfprobeAudioProbe,
    FfprobeValidator,
)
from short_video_generator.rendering.subtitles import AssSubtitleProvider
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


def build_manual_pipeline(
    settings: Settings,
    production_input: ManualProductionInput | None = None,
    tts_provider: TextToSpeechProvider | None = None,
    asset_provider: AssetProvider | None = None,
    caption_alignment_provider: CaptionAlignmentProvider | None = None,
    character_provider: CharacterAssetProvider | None = None,
) -> ManualPipeline:
    if settings.ffmpeg_path is None:
        raise RuntimeError("FFmpeg not found; set SVG_FFMPEG_PATH or add ffmpeg to PATH")
    if settings.ffprobe_path is None:
        raise RuntimeError("ffprobe not found; set SVG_FFPROBE_PATH or add ffprobe to PATH")
    production_input = production_input or ManualProductionInput(
        topic="How does a local video pipeline work?",
        language="en",
        target_duration_seconds=30,
    )
    speech = tts_provider or _build_tts_provider(settings)
    assets = asset_provider or _build_asset_provider(settings)
    captions = caption_alignment_provider or _build_caption_alignment_provider(settings)
    characters = character_provider or LocalCharacterAssetProvider(
        settings.project_root / "assets" / "characters"
    )
    engine = build_engine(settings)
    create_schema(engine)
    sessions = session_factory(engine)
    repository = SqlAlchemyExecutionRepository(sessions)
    store = LocalArtifactStore(settings.storage_root)
    media_workflow = NarratedMediaWorkflow(
        steps=StepExecutor(repository),
        store=store,
        speech=speech,
        speech_options=TextToSpeechOptions(
            voice=(
                settings.elevenlabs_voice_id
                if settings.tts_provider == "elevenlabs"
                else settings.tts_voice
            ),
            voice_version=settings.elevenlabs_voice_version,
            model_id=settings.elevenlabs_model_id,
            rate=settings.tts_rate,
            volume=settings.tts_volume,
            stability=settings.elevenlabs_stability,
            similarity_boost=settings.elevenlabs_similarity_boost,
            style=settings.elevenlabs_style,
            use_speaker_boost=settings.elevenlabs_use_speaker_boost,
            speed=settings.elevenlabs_speed,
        ),
        language=production_input.language,
        audio_probe=FfprobeAudioProbe(settings.ffprobe_path),
        assets=assets,
        caption_alignment=captions,
        characters=characters,
        default_character_id=settings.default_character_id,
        tts_mode=settings.tts_mode,
        subtitles=AssSubtitleProvider(),
        renderer=FfmpegRenderer(settings.ffmpeg_path, settings.storage_root),
    )
    topic_hash = hashlib.sha256(
        f"{production_input.topic}|{production_input.language}".encode()
    ).hexdigest()[:16]
    candidate = CandidateInput(
        external_id=f"manual-{topic_hash}",
        title=production_input.topic,
        summary=_topic_summary(production_input),
        canonical_url=f"https://example.test/manual/{topic_hash}",
        source_payload={"manual": True, **production_input.model_dump(mode="json")},
    )
    fingerprint = _input_fingerprint(
        production_input, settings, speech, assets, captions, characters
    )
    return ManualPipeline(
        repository=repository,
        store=store,
        source=FixtureSourceProvider([candidate]),
        evaluator=DeterministicCandidateEvaluator(),
        editorial=DeterministicEditorialProvider(
            production_input.language,
            production_input.target_duration_seconds,
            settings.default_character_id,
        ),
        media_workflow=media_workflow,
        validator=FfprobeValidator(settings.ffprobe_path),
        input_fingerprint=fingerprint,
    )


def default_idempotency_key(
    production_input: ManualProductionInput, settings: Settings
) -> str:
    payload = {
        "input": production_input.model_dump(mode="json"),
        "tts_provider": settings.tts_provider,
        "tts_voice": settings.tts_voice,
        "tts_rate": settings.tts_rate,
        "tts_volume": settings.tts_volume,
        "elevenlabs_voice_id": settings.elevenlabs_voice_id,
        "elevenlabs_voice_version": settings.elevenlabs_voice_version,
        "elevenlabs_model_id": settings.elevenlabs_model_id,
        "elevenlabs_stability": settings.elevenlabs_stability,
        "elevenlabs_similarity_boost": settings.elevenlabs_similarity_boost,
        "elevenlabs_style": settings.elevenlabs_style,
        "elevenlabs_use_speaker_boost": settings.elevenlabs_use_speaker_boost,
        "elevenlabs_speed": settings.elevenlabs_speed,
        "asset_provider": settings.asset_provider,
        "default_character_id": settings.default_character_id,
        "caption_alignment_provider": settings.caption_alignment_provider,
        "whisperx_model": settings.whisperx_model,
        "whisperx_device": settings.whisperx_device,
        "visual_planner_version": "visual-direction-v1",
        "byte_choreography_version": "byte-choreography-v1",
        "visual_ranking_version": "visual-ranking-v1",
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:20]
    return f"manual-{digest}"


def _build_tts_provider(settings: Settings) -> TextToSpeechProvider:
    if settings.tts_provider == "fake":
        return FakeTextToSpeechProvider()
    if settings.tts_provider == "edge":
        return EdgeTextToSpeechProvider()
    if settings.tts_provider == "elevenlabs":
        return ElevenLabsTextToSpeechProvider(
            api_key=settings.elevenlabs_api_key,
            voice_id=settings.elevenlabs_voice_id,
            model_id=settings.elevenlabs_model_id,
            voice_version=settings.elevenlabs_voice_version,
        )
    raise ValueError(f"Unsupported TTS provider: {settings.tts_provider}")


def _build_asset_provider(settings: Settings) -> AssetProvider:
    if settings.asset_provider == "fake":
        return FakeAssetProvider()
    if settings.asset_provider == "pexels":
        if settings.pexels_api_key is None:
            raise RuntimeError("PEXELS_API_KEY is required when ASSET_PROVIDER=pexels")
        return PexelsAssetProvider(settings.pexels_api_key)
    raise ValueError(f"Unsupported asset provider: {settings.asset_provider}")


def _build_caption_alignment_provider(settings: Settings) -> CaptionAlignmentProvider:
    if settings.caption_alignment_provider == "fake":
        return FakeCaptionAlignmentProvider()
    if settings.caption_alignment_provider == "whisperx":
        return WhisperXCaptionAlignmentProvider(
            model_name=settings.whisperx_model,
            device=settings.whisperx_device,
        )
    raise ValueError(
        f"Unsupported caption alignment provider: {settings.caption_alignment_provider}"
    )


def _input_fingerprint(
    production_input: ManualProductionInput,
    settings: Settings,
    speech: TextToSpeechProvider,
    assets: AssetProvider,
    captions: CaptionAlignmentProvider,
    characters: CharacterAssetProvider,
) -> str:
    payload = {
        "input": production_input.model_dump(mode="json"),
        "tts": {
            "provider": speech.provider_name,
            "version": speech.provider_version,
            "voice": settings.tts_voice,
            "rate": settings.tts_rate,
            "volume": settings.tts_volume,
            "voice_version": settings.elevenlabs_voice_version,
            "model_id": settings.elevenlabs_model_id,
            "stability": settings.elevenlabs_stability,
            "similarity_boost": settings.elevenlabs_similarity_boost,
            "style": settings.elevenlabs_style,
            "use_speaker_boost": settings.elevenlabs_use_speaker_boost,
            "speed": settings.elevenlabs_speed,
        },
        "assets": {
            "provider": assets.provider_name,
            "version": assets.provider_version,
            "strategy": assets.selection_strategy_version,
        },
        "characters": {
            "provider": characters.provider_name,
            "version": characters.provider_version,
            "default_character_id": settings.default_character_id,
        },
        "captions": {
            "provider": captions.provider_name,
            "version": captions.provider_version,
            "whisperx_model": settings.whisperx_model,
            "whisperx_device": settings.whisperx_device,
        },
        "visuals": {
            "planner": "visual-direction-v1",
            "choreography": "byte-choreography-v1",
            "ranking": "visual-ranking-v1",
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _topic_summary(production_input: ManualProductionInput) -> str:
    if production_input.language.lower().startswith("es"):
        return (
            f"{production_input.topic} se entiende por su propósito principal, cómo funciona "
            "y cuándo resulta útil."
        )
    return (
        f"{production_input.topic} can be understood through its main purpose, how it works, "
        "and when it is useful."
    )
