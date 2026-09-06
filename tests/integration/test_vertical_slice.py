import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from short_video_generator.api.app import create_app
from short_video_generator.bootstrap import build_manual_pipeline
from short_video_generator.config import Settings
from short_video_generator.domain.enums import ArtifactType, ProductionStatus, StepStatus
from short_video_generator.persistence.database import build_engine, session_factory
from short_video_generator.persistence.models import (
    ArtifactRecord,
    PipelineRunRecord,
    ProductionRecord,
    StepRunRecord,
    TopicCandidateRecord,
)


def test_complete_vertical_slice_is_idempotent_and_reviewable(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        database_path=tmp_path / "data" / "app.db",
        storage_root=tmp_path / "storage",
        ffmpeg_path=_required_executable("SVG_FFMPEG_PATH", "ffmpeg"),
        ffprobe_path=_required_executable("SVG_FFPROBE_PATH", "ffprobe"),
    )
    pipeline = build_manual_pipeline(settings)

    first = pipeline.execute("integration-fixture")
    second = pipeline.execute("integration-fixture")

    assert first.status == ProductionStatus.AWAITING_REVIEW
    assert not first.reused
    assert second.reused
    assert second.run_id == first.run_id
    assert second.production_id == first.production_id

    engine = build_engine(settings)
    sessions = session_factory(engine)
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(PipelineRunRecord)) == 1
        assert session.scalar(select(func.count()).select_from(TopicCandidateRecord)) == 1
        assert session.scalar(select(func.count()).select_from(ProductionRecord)) == 1
        assert session.scalar(select(func.count()).select_from(StepRunRecord)) == 9
        assert session.scalar(select(func.count()).select_from(ArtifactRecord)) == 7
        assert set(session.scalars(select(StepRunRecord.status))) == {StepStatus.COMPLETED}
        artifacts = session.scalars(select(ArtifactRecord)).all()
        render = next(item for item in artifacts if item.type == ArtifactType.RENDER)
        assert (settings.storage_root / render.relative_path).is_file()
        assert all((settings.storage_root / item.relative_path).is_file() for item in artifacts)
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
