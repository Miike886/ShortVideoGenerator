import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from short_video_generator.contracts import LocalFileDraft
from short_video_generator.domain.enums import ArtifactType


class FakeAssetProvider:
    provider_name = "fake-solid-background"
    provider_version = "1"
    selection_strategy_version = "scene-color-v1"
    width = 540
    height = 960
    colors = ((31, 41, 55), (30, 64, 175), (88, 28, 135))

    def __init__(self) -> None:
        self.calls = 0

    def acquire(
        self, visual_query: str, scene_order: int, destination: Path
    ) -> LocalFileDraft:
        self.calls += 1
        if not visual_query.strip():
            raise ValueError("Asset visual query cannot be empty")
        destination.mkdir(parents=True, exist_ok=True)
        filename = f"scene-{scene_order:02d}.ppm"
        output = destination / filename
        color = self.colors[(scene_order - 1) % len(self.colors)]
        header = f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
        output.write_bytes(header + bytes(color) * (self.width * self.height))
        return LocalFileDraft(
            artifact_type=ArtifactType.IMAGE,
            relative_path=Path(filename),
            media_type="image/x-portable-pixmap",
            metadata={
                "provider": self.provider_name,
                "provider_version": self.provider_version,
                "external_asset_id": f"fake-scene-{scene_order}",
                "source_url": None,
                "download_url": None,
                "creator": "ShortVideoGenerator fixture",
                "creator_url": None,
                "width": self.width,
                "height": self.height,
                "duration_seconds": None,
                "visual_query": visual_query,
                "selection_strategy": self.selection_strategy_version,
                "fixture": True,
            },
        )


class PexelsAssetProvider:
    provider_name = "pexels"
    provider_version = "v1"
    selection_strategy_version = "portrait-video-landscape-video-photo-v1"
    api_root = "https://api.pexels.com/v1"

    def __init__(
        self,
        api_key: str,
        fallback: FakeAssetProvider | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        if not api_key.strip():
            raise ValueError("PEXELS_API_KEY is required for the Pexels provider")
        self.api_key = api_key
        self.fallback = fallback or FakeAssetProvider()
        self.timeout_seconds = timeout_seconds

    def acquire(
        self, visual_query: str, scene_order: int, destination: Path
    ) -> LocalFileDraft:
        query = " ".join(visual_query.split())
        if not query:
            raise ValueError("Asset visual query cannot be empty")
        for attempted_query in _query_attempts(query):
            selected = self._search(attempted_query)
            if selected is not None:
                return self._download(selected, attempted_query, scene_order, destination)
        fallback = self.fallback.acquire(query, scene_order, destination)
        return fallback.model_copy(
            update={
                "metadata": fallback.metadata
                | {
                    "fallback_from": self.provider_name,
                    "fallback_reason": "no_results",
                }
            }
        )

    def _search(self, query: str) -> dict[str, object] | None:
        for orientation in ("portrait", "landscape"):
            payload = self._request_json(
                "/videos/search",
                {"query": query, "orientation": orientation, "per_page": "5"},
            )
            videos = payload.get("videos", [])
            if videos:
                return self._select_video(videos[0], orientation)
        payload = self._request_json(
            "/search", {"query": query, "orientation": "portrait", "per_page": "5"}
        )
        photos = payload.get("photos", [])
        return self._select_photo(photos[0]) if photos else None

    def _request_json(
        self, path: str, parameters: dict[str, str]
    ) -> dict[str, object]:
        url = f"{self.api_root}{path}?{urllib.parse.urlencode(parameters)}"
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": self.api_key,
                "User-Agent": "ShortVideoGenerator/0.1",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Pexels request failed for {path}: {error}") from error

    @staticmethod
    def _select_video(video: dict[str, object], orientation: str) -> dict[str, object]:
        files = [
            item
            for item in video.get("video_files", [])
            if item.get("file_type") == "video/mp4"
            and item.get("width")
            and item.get("height")
        ]
        if not files:
            raise ValueError(f"Pexels video {video.get('id')} has no usable MP4 file")
        target_width, target_height = (
            (1080, 1920) if orientation == "portrait" else (1920, 1080)
        )
        target_area = target_width * target_height
        selected_file = max(
            files,
            key=lambda item: (
                item["width"] >= target_width and item["height"] >= target_height,
                -abs((item["width"] * item["height"]) - target_area),
            ),
        )
        user = video.get("user") or {}
        return {
            "artifact_type": ArtifactType.VIDEO_CLIP,
            "extension": ".mp4",
            "media_type": "video/mp4",
            "external_asset_id": str(video["id"]),
            "source_url": video.get("url"),
            "download_url": selected_file["link"],
            "creator": user.get("name"),
            "creator_url": user.get("url"),
            "width": selected_file["width"],
            "height": selected_file["height"],
            "duration_seconds": video.get("duration"),
            "orientation": orientation,
        }

    @staticmethod
    def _select_photo(photo: dict[str, object]) -> dict[str, object]:
        sources = photo.get("src") or {}
        download_url = sources.get("large2x") or sources.get("large")
        if not download_url:
            raise ValueError(f"Pexels photo {photo.get('id')} has no usable image URL")
        return {
            "artifact_type": ArtifactType.IMAGE,
            "extension": ".jpg",
            "media_type": "image/jpeg",
            "external_asset_id": str(photo["id"]),
            "source_url": photo.get("url"),
            "download_url": download_url,
            "creator": photo.get("photographer"),
            "creator_url": photo.get("photographer_url"),
            "width": photo.get("width"),
            "height": photo.get("height"),
            "duration_seconds": None,
            "orientation": "portrait",
        }

    def _download(
        self,
        selected: dict[str, object],
        query: str,
        scene_order: int,
        destination: Path,
    ) -> LocalFileDraft:
        destination.mkdir(parents=True, exist_ok=True)
        filename = f"scene-{scene_order:02d}{selected['extension']}"
        output = destination / filename
        partial = output.with_suffix(output.suffix + ".partial")
        request = urllib.request.Request(
            str(selected["download_url"]),
            headers={"User-Agent": "ShortVideoGenerator/0.1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                partial.write_bytes(response.read())
            partial.replace(output)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise RuntimeError(
                f"Pexels asset download failed for {selected['external_asset_id']}: {error}"
            ) from error
        metadata = {
            "provider": self.provider_name,
            "provider_version": self.provider_version,
            "visual_query": query,
            "selection_strategy": self.selection_strategy_version,
        } | {key: value for key, value in selected.items() if key != "artifact_type"}
        return LocalFileDraft(
            artifact_type=selected["artifact_type"],
            relative_path=Path(filename),
            media_type=str(selected["media_type"]),
            metadata=metadata,
        )


def _query_attempts(query: str) -> tuple[str, ...]:
    simplified = " ".join(query.split()[:3])
    return (query,) if simplified == query else (query, simplified)
