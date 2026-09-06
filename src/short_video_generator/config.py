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

    @classmethod
    def local(cls, project_root: Path | None = None) -> "Settings":
        root = (project_root or Path.cwd()).resolve()
        return cls(
            project_root=root,
            database_path=root / "data" / "app.db",
            storage_root=root / "storage",
            ffmpeg_path=_resolve_executable("SVG_FFMPEG_PATH", "ffmpeg"),
            ffprobe_path=_resolve_executable("SVG_FFPROBE_PATH", "ffprobe"),
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
