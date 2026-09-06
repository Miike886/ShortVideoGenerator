import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    project_root: Path
    database_path: Path
    storage_root: Path
    ffmpeg_path: Path | None = None
    ffprobe_path: Path | None = None
    tts_provider: str = "fake"
    tts_voice: str | None = None
    tts_rate: int = 0
    tts_volume: int = 100
    asset_provider: str = "fake"
    pexels_api_key: str | None = None
    default_character_id: str = "byte"
    caption_alignment_provider: str = "fake"
    whisperx_model: str = "small"
    whisperx_device: str = "cpu"

    @classmethod
    def local(cls, project_root: Path | None = None) -> "Settings":
        root = (project_root or Path.cwd()).resolve()
        return cls(
            project_root=root,
            database_path=root / "data" / "app.db",
            storage_root=root / "storage",
            ffmpeg_path=_resolve_executable("SVG_FFMPEG_PATH", "ffmpeg"),
            ffprobe_path=_resolve_executable("SVG_FFPROBE_PATH", "ffprobe"),
            tts_provider=os.environ.get(
                "TTS_PROVIDER", os.environ.get("SVG_TTS_PROVIDER", "fake")
            ),
            tts_voice=os.environ.get("TTS_VOICE", os.environ.get("SVG_TTS_VOICE"))
            or None,
            tts_rate=int(
                os.environ.get("TTS_RATE", os.environ.get("SVG_TTS_RATE", "0"))
            ),
            tts_volume=int(
                os.environ.get("TTS_VOLUME", os.environ.get("SVG_TTS_VOLUME", "100"))
            ),
            asset_provider=os.environ.get("ASSET_PROVIDER", "fake"),
            pexels_api_key=os.environ.get("PEXELS_API_KEY") or None,
            default_character_id=os.environ.get("DEFAULT_CHARACTER_ID", "byte"),
            caption_alignment_provider=os.environ.get(
                "CAPTION_ALIGNMENT_PROVIDER", "fake"
            ),
            whisperx_model=os.environ.get("WHISPERX_MODEL", "small"),
            whisperx_device=os.environ.get("WHISPERX_DEVICE", "cpu"),
        )

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"


def _resolve_executable(environment_name: str, command: str) -> Path | None:
    configured = os.environ.get(environment_name)
    if configured:
        return Path(configured).expanduser().resolve()
    discovered = shutil.which(command)
    return Path(discovered).resolve() if discovered else None
