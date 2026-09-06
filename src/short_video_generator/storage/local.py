import hashlib
import shutil
from pathlib import Path

from short_video_generator.pipeline.models import StoredFile


class LocalArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.assets_root = self.root / "assets"
        self.renders_root = self.root / "renders"
        self.work_root = self.root / "work"
        for directory in (self.assets_root, self.renders_root, self.work_root):
            directory.mkdir(parents=True, exist_ok=True)

    def prepare_work_directory(self, run_id: str) -> Path:
        directory = self.work_root / run_id
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)
        return directory

    def asset_directory(self, production_id: str) -> Path:
        directory = self.assets_root / production_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def render_directory(self, production_id: str) -> Path:
        directory = self.renders_root / production_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def promote(self, source: Path, destination: Path) -> StoredFile:
        source = source.resolve()
        destination = destination.resolve()
        self._require_inside(source, self.work_root)
        self._require_inside(destination, self.root)
        if not source.is_file():
            raise FileNotFoundError(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_destination = destination.with_suffix(destination.suffix + ".partial")
        shutil.copyfile(source, temporary_destination)
        temporary_destination.replace(destination)
        return self.describe(destination)

    def resolve(self, relative_path: Path) -> Path:
        absolute = (self.root / relative_path).resolve()
        self._require_inside(absolute, self.root)
        return absolute

    def write_text(self, directory: Path, filename: str, content: str) -> Path:
        directory = directory.resolve()
        self._require_inside(directory, self.work_root)
        destination = (directory / filename).resolve()
        self._require_inside(destination, directory)
        destination.write_text(content, encoding="utf-8")
        return destination

    def describe(self, path: Path) -> StoredFile:
        absolute = path.resolve()
        self._require_inside(absolute, self.root)
        digest = hashlib.sha256()
        with absolute.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return StoredFile(
            relative_path=absolute.relative_to(self.root),
            absolute_path=absolute,
            size_bytes=absolute.stat().st_size,
            sha256=digest.hexdigest(),
        )

    def cleanup_work_directory(self, run_id: str) -> None:
        directory = (self.work_root / run_id).resolve()
        self._require_inside(directory, self.work_root)
        if directory.exists():
            shutil.rmtree(directory)

    @staticmethod
    def _require_inside(path: Path, parent: Path) -> None:
        try:
            path.relative_to(parent.resolve())
        except ValueError as error:
            raise ValueError(f"Path {path} escapes {parent}") from error
