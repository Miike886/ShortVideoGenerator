from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    project_root: Path
    database_path: Path
    storage_root: Path

    @classmethod
    def local(cls, project_root: Path | None = None) -> "Settings":
        root = (project_root or Path.cwd()).resolve()
        return cls(
            project_root=root,
            database_path=root / "data" / "app.db",
            storage_root=root / "storage",
        )

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"

