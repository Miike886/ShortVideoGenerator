import hashlib

from short_video_generator.domain.enums import ArtifactType
from short_video_generator.providers.assets import FakeAssetProvider, PexelsAssetProvider


def test_fake_asset_provider_returns_attributable_deterministic_artifact(tmp_path) -> None:
    first_provider = FakeAssetProvider()
    second_provider = FakeAssetProvider()
    first = first_provider.acquire("developer laptop", 1, tmp_path / "first")
    second = second_provider.acquire("developer laptop", 1, tmp_path / "second")

    assert first.artifact_type == ArtifactType.IMAGE
    assert first.metadata["provider"] == first_provider.provider_name
    assert first.metadata["external_asset_id"] == "fake-scene-1"
    assert first.metadata["creator"]
    assert _sha256(tmp_path / "first" / first.relative_path) == _sha256(
        tmp_path / "second" / second.relative_path
    )


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EmptyPexelsProvider(PexelsAssetProvider):
    def _request_json(self, path, parameters):
        del parameters
        return {"videos": []} if "videos" in path else {"photos": []}


def test_pexels_no_results_uses_deterministic_fallback_without_network(tmp_path) -> None:
    fallback = FakeAssetProvider()
    provider = EmptyPexelsProvider("test-key", fallback=fallback)

    asset = provider.acquire("specific unavailable query", 2, tmp_path)

    assert fallback.calls == 1
    assert asset.metadata["fallback_from"] == "pexels"
    assert asset.metadata["fallback_reason"] == "no_results"
