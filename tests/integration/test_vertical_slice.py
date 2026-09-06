import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from short_video_generator.api.app import create_app
from short_video_generator.bootstrap import build_manual_pipeline
from short_video_generator.config import Settings
from short_video_generator.contracts import ManualProductionInput
from short_video_generator.domain.enums import ArtifactType, ProductionStatus, StepStatus
from short_video_generator.persistence.database import build_engine, session_factory
from short_video_generator.persistence.models import (
    ArtifactRecord,
    PipelineRunRecord,
    ProductionRecord,
    StepRunRecord,
    TopicCandidateRecord,
)
from short_video_generator.providers.assets import FakeAssetProvider
from short_video_generator.providers.characters import LocalCharacterAssetProvider
from short_video_generator.providers.tts import FakeTextToSpeechProvider
from short_video_generator.rendering import FfprobeAudioProbe


def test_complete_vertical_slice_is_idempotent_and_reviewable(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        database_path=tmp_path / "data" / "app.db",
        storage_root=tmp_path / "storage",
        ffmpeg_path=_required_executable("SVG_FFMPEG_PATH", "ffmpeg"),
        ffprobe_path=_required_executable("SVG_FFPROBE_PATH", "ffprobe"),
    )
    tts = FakeTextToSpeechProvider()
    assets = FakeAssetProvider()
    characters = LocalCharacterAssetProvider(Path("assets/characters"))
    pipeline = build_manual_pipeline(
        settings,
        ManualProductionInput(
            topic="Why do programmers use Docker?",
            language="en",
            target_duration_seconds=30,
        ),
        tts_provider=tts,
        asset_provider=assets,
        character_provider=characters,
    )

    first = pipeline.execute("integration-fixture")
    engine = build_engine(settings)
    sessions = session_factory(engine)
    with sessions() as session:
        first_artifact_ids = {
            item.relative_path: item.id for item in session.scalars(select(ArtifactRecord)).all()
        }
    second = pipeline.execute("integration-fixture")

    assert first.status == ProductionStatus.AWAITING_REVIEW
    assert not first.reused
    assert second.reused
    assert second.run_id == first.run_id
    assert second.production_id == first.production_id
    assert tts.calls == 1
    assert assets.calls == 5
    changed_pipeline = build_manual_pipeline(
        settings,
        ManualProductionInput(topic="A different topic", language="en"),
        tts_provider=tts,
        asset_provider=assets,
        character_provider=characters,
    )
    with pytest.raises(ValueError, match="different production inputs"):
        changed_pipeline.execute("integration-fixture")

    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(PipelineRunRecord)) == 1
        assert session.scalar(select(func.count()).select_from(TopicCandidateRecord)) == 1
        assert session.scalar(select(func.count()).select_from(ProductionRecord)) == 1
        assert session.scalar(select(func.count()).select_from(StepRunRecord)) == 14
        assert session.scalar(select(func.count()).select_from(ArtifactRecord)) == 13
        assert set(session.scalars(select(StepRunRecord.status))) == {StepStatus.COMPLETED}
        step_records = session.scalars(select(StepRunRecord)).all()
        fingerprinted_steps = {
            "generate_audio",
            "plan_timeline",
            "resolve_presenters",
            "generate_assets",
            "align_captions",
            "generate_subtitles",
        }
        for step in step_records:
            if step.step in fingerprinted_steps:
                assert len(step.input_summary["fingerprint"]) == 64
            assert step.output_summary["reused"] is True
        artifacts = session.scalars(select(ArtifactRecord)).all()
        assert {item.relative_path: item.id for item in artifacts} == first_artifact_ids
        render = next(item for item in artifacts if item.type == ArtifactType.RENDER)
        voice = next(item for item in artifacts if item.type == ArtifactType.VOICE)
        timeline = next(item for item in artifacts if item.type == ArtifactType.TIMELINE)
        alignment = next(item for item in artifacts if item.type == ArtifactType.CAPTION_ALIGNMENT)
        character_reference = next(
            item for item in artifacts if item.type == ArtifactType.CHARACTER_REFERENCE
        )
        subtitle = next(item for item in artifacts if item.type == ArtifactType.SUBTITLE)
        visual_plan = next(item for item in artifacts if item.type == ArtifactType.VISUAL_PLAN)
        assert visual_plan.artifact_metadata["planner"] == "visual-direction-v1"
        assert len(visual_plan.artifact_metadata["plans"]) == 5
        for artifact in (voice, timeline, alignment, character_reference, subtitle, render):
            assert len(artifact.artifact_metadata["input_fingerprint"]) == 64
        production = session.scalar(select(ProductionRecord))
        assert production is not None
        assert [scene["role"] for scene in production.script["scenes"]] == [
            "hook",
            "context",
            "fact",
            "development",
            "conclusion",
        ]
        presenters = [
            scene["presenter"]
            for scene in production.script["scenes"]
            if scene["presenter"] is not None
        ]
        assert len(presenters) == len(production.script["scenes"])
        assert [presenter["pose"] for presenter in presenters] == [
            "explaining",
            "thinking",
            "surprised",
            "pointing_left",
            "happy",
        ]
        presenter_refs = character_reference.artifact_metadata["presenters"]
        assert {item["character_id"] for item in presenter_refs} == {"byte"}
        assert {item["pose"] for item in presenter_refs} == {
            "explaining",
            "thinking",
            "surprised",
            "pointing_left",
            "happy",
        }
        scene_duration = sum(scene["duration_seconds"] for scene in production.script["scenes"])
        audio_probe = FfprobeAudioProbe(settings.ffprobe_path).inspect(
            settings.storage_root / voice.relative_path
        )
        assert scene_duration == pytest.approx(audio_probe.duration_seconds, abs=0.001)
        assert timeline.artifact_metadata["duration_seconds"] == pytest.approx(
            audio_probe.duration_seconds
        )
        assert alignment.artifact_metadata["word_count"] > 0
        last_word = alignment.artifact_metadata["words"][-1]
        assert last_word["end_seconds"] == pytest.approx(audio_probe.duration_seconds, abs=0.002)
        subtitle_text = (settings.storage_root / subtitle.relative_path).read_text(encoding="utf-8")
        assert Path(subtitle.relative_path).suffix == ".ass"
        assert "Dialogue:" in subtitle_text
        assert r"{\c&H0000D7FF&}" in subtitle_text
        assert subtitle.artifact_metadata["caption_group_count"] > 1
        assert (settings.storage_root / render.relative_path).is_file()
        assert all((settings.storage_root / item.relative_path).is_file() for item in artifacts)
        checks = {check["name"]: check for check in production.validation_report["checks"]}
        assert checks["video_codec"]["detail"] == "h264"
        assert checks["audio_codec"]["detail"] == "aac"
        assert checks["duration"]["passed"] is True
    engine.dispose()
    assert not (settings.storage_root / "work" / first.run_id).exists()

    with TestClient(create_app(settings)) as client:
        queue = client.get("/review-queue")
        assert queue.status_code == 200
        assert len(queue.json()) == 1
        item = queue.json()[0]
        assert item["id"] == first.production_id
        assert item["validation_report"]["passed"] is True
        assert any(artifact["type"] == "render" for artifact in item["artifacts"])

        decision = client.post(
            f"/productions/{first.production_id}/reviews",
            json={"decision": "approved", "comment": "Fixture reviewed"},
        )
        assert decision.status_code == 200
        assert decision.json()["status"] == "approved"
        assert client.get("/review-queue").json() == []


def _required_executable(environment_name: str, command: str) -> Path:
    configured = os.environ.get(environment_name)
    discovered = configured or shutil.which(command)
    if not discovered:
        pytest.skip(f"{command} is not installed or configured")
    path = Path(discovered).resolve()
    if not path.is_file():
        pytest.skip(f"{command} executable does not exist: {path}")
    return path
