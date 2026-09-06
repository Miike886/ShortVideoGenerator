import pytest
from fastapi.testclient import TestClient

from short_video_generator.api.app import create_app
from short_video_generator.config import Settings
from short_video_generator.domain.enums import (
    CandidateStatus,
    ProductionStatus,
    RunStatus,
    RunTrigger,
)
from short_video_generator.persistence.database import build_engine, create_schema, session_factory
from short_video_generator.persistence.models import (
    NicheRecord,
    PipelineRunRecord,
    ProductionRecord,
    SourceConfigRecord,
    TopicCandidateRecord,
)


def test_health_endpoint(tmp_path) -> None:
    with TestClient(create_app(Settings.local(tmp_path))) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("decision", ["approved", "rejected", "changes_requested"])
def test_review_endpoint_accepts_every_human_decision(tmp_path, decision: str) -> None:
    settings = Settings.local(tmp_path)
    engine = build_engine(settings)
    create_schema(engine)
    sessions = session_factory(engine)
    with sessions() as session:
        niche = NicheRecord(name="test", description="test")
        session.add(niche)
        session.flush()
        source = SourceConfigRecord(
            niche_id=niche.id,
            type="fixture",
            name="fixture",
        )
        run = PipelineRunRecord(
            niche_id=niche.id,
            idempotency_key=f"review-{decision}",
            trigger=RunTrigger.MANUAL,
            status=RunStatus.COMPLETED,
        )
        session.add_all([source, run])
        session.flush()
        candidate = TopicCandidateRecord(
            pipeline_run_id=run.id,
            source_config_id=source.id,
            external_id="candidate",
            canonical_url="https://example.test/candidate",
            title="Candidate",
            summary="Summary",
            fingerprint="0" * 64,
            status=CandidateStatus.SELECTED,
        )
        session.add(candidate)
        session.flush()
        production = ProductionRecord(
            pipeline_run_id=run.id,
            topic_candidate_id=candidate.id,
            status=ProductionStatus.AWAITING_REVIEW,
            brief={},
            script={},
            validation_report={},
        )
        session.add(production)
        session.commit()
        production_id = production.id
    engine.dispose()

    with TestClient(create_app(settings)) as client:
        response = client.post(
            f"/productions/{production_id}/reviews",
            json={"decision": decision, "comment": "Human decision"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == decision
