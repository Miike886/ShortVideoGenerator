from pathlib import Path
from typing import Protocol

from short_video_generator.contracts import (
    AudioArtifactMetadata,
    CandidateEvaluation,
    CandidateInput,
    CaptionAlignmentResult,
    CharacterAssetReference,
    EditorialBrief,
    LocalFileDraft,
    PresenterInstruction,
    RenderRequest,
    RenderResult,
    TextToSpeechOptions,
    VideoScript,
)


class SourceProvider(Protocol):
    def fetch(self, niche: str) -> list[CandidateInput]: ...


class CandidateEvaluator(Protocol):
    def evaluate(self, candidate: CandidateInput) -> CandidateEvaluation: ...


class EditorialProvider(Protocol):
    def create_brief(self, candidate: CandidateInput) -> EditorialBrief: ...

    def create_script(self, brief: EditorialBrief) -> VideoScript: ...


class TextToSpeechProvider(Protocol):
    provider_name: str
    provider_version: str
    output_suffix: str
    output_media_type: str

    def synthesize(
        self,
        text: str,
        output_path: Path,
        language: str,
        options: TextToSpeechOptions,
    ) -> AudioArtifactMetadata: ...


class AssetProvider(Protocol):
    provider_name: str
    provider_version: str
    selection_strategy_version: str

    def acquire(
        self, visual_query: str, scene_order: int, destination: Path
    ) -> LocalFileDraft: ...


class CharacterAssetProvider(Protocol):
    provider_name: str
    provider_version: str

    def resolve(
        self, instruction: PresenterInstruction, scene_order: int
    ) -> CharacterAssetReference: ...


class CaptionAlignmentProvider(Protocol):
    provider_name: str
    provider_version: str

    def align(
        self,
        audio_path: Path,
        script: VideoScript,
        duration_seconds: float,
    ) -> CaptionAlignmentResult: ...


class Renderer(Protocol):
    def render(self, request: RenderRequest, destination: Path) -> RenderResult: ...
