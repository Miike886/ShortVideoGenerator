from fastapi.testclient import TestClient

from short_video_generator.api.app import create_app


def test_health_endpoint() -> None:
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

