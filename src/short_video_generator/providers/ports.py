from pathlib import Path
from typing import Protocol

from short_video_generator.contracts import (
    CandidateInput,
    EditorialBrief,
    GeneratedAsset,
    RenderRequest,
    RenderResult,
    VideoScript,
)


class SourceProvider(Protocol):
    def fetch(self, niche: str) -> list[CandidateInput]: ...


class EditorialProvider(Protocol):
    def create_brief(self, candidate: CandidateInput) -> EditorialBrief: ...

    def create_script(self, brief: EditorialBrief) -> VideoScript: ...


class SpeechProvider(Protocol):
    def synthesize(self, text: str, destination: Path) -> GeneratedAsset: ...


class MediaProvider(Protocol):
    def create_visuals(self, script: VideoScript, destination: Path) -> list[GeneratedAsset]: ...


class Renderer(Protocol):
    def render(self, request: RenderRequest, destination: Path) -> RenderResult: ...

