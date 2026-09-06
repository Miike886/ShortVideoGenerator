import importlib.metadata
import re
from pathlib import Path

from short_video_generator.contracts import (
    CaptionAlignmentResult,
    VideoScript,
    WordTiming,
)

_WORD_PATTERN = re.compile(r"[\w']+", re.UNICODE)


class FakeCaptionAlignmentProvider:
    provider_name = "fake-known-text-aligner"
    provider_version = "word-even-v1"

    def align(
        self,
        audio_path: Path,
        script: VideoScript,
        duration_seconds: float,
    ) -> CaptionAlignmentResult:
        del audio_path
        words = _script_words(script)
        if not words:
            raise ValueError("Cannot align captions for a script with no words")
        slot = duration_seconds / len(words)
        timings = tuple(
            WordTiming(
                word=word,
                start_seconds=round(index * slot, 3),
                end_seconds=round((index + 1) * slot, 3),
            )
            for index, word in enumerate(words)
        )
        final = timings[-1].model_copy(update={"end_seconds": round(duration_seconds, 3)})
        return CaptionAlignmentResult(
            words=timings[:-1] + (final,),
            duration_seconds=round(duration_seconds, 3),
            provider=self.provider_name,
            provider_version=self.provider_version,
        )


class WhisperXCaptionAlignmentProvider:
    provider_name = "whisperx"

    def __init__(self, model_name: str = "small", device: str = "cpu") -> None:
        self.model_name = model_name
        self.device = device
        try:
            self.provider_version = importlib.metadata.version("whisperx")
        except importlib.metadata.PackageNotFoundError:
            self.provider_version = "unavailable"

    def align(
        self,
        audio_path: Path,
        script: VideoScript,
        duration_seconds: float,
    ) -> CaptionAlignmentResult:
        try:
            import whisperx  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError(
                "WhisperX is not installed. Install it separately and set "
                "CAPTION_ALIGNMENT_PROVIDER=whisperx to use the real aligner."
            ) from error

        del whisperx
        raise NotImplementedError(
            "WhisperX integration is intentionally isolated behind "
            "CaptionAlignmentProvider; wire model loading/alignment here when the local "
            "ML runtime is available."
        )


def _script_words(script: VideoScript) -> tuple[str, ...]:
    text = " ".join(scene.narration for scene in script.scenes)
    return tuple(match.group(0) for match in _WORD_PATTERN.finditer(text))
