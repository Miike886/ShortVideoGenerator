import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from short_video_generator.contracts import (
    CharacterAssetReference,
    GeneratedAsset,
    RenderRequest,
    RenderResult,
    ValidationCheck,
    ValidationReport,
)
from short_video_generator.domain.enums import ArtifactType


@dataclass(frozen=True, slots=True)
class PresenterLayout:
    margin_x: int = 72
    subtitle_safe_bottom: int = 320
    fade_seconds: float = 0.25


class MissingMediaExecutable(RuntimeError):
    pass


class FfmpegRenderer:
    def __init__(
        self, executable: Path, storage_root: Path, presenter_layout: PresenterLayout | None = None
    ) -> None:
        self.executable = executable
        self.storage_root = storage_root.resolve()
        self.presenter_layout = presenter_layout or PresenterLayout()

    def render(self, request: RenderRequest, destination: Path) -> RenderResult:
        self._require_executable()
        destination.mkdir(parents=True, exist_ok=True)
        output = destination / "final.mp4"
        visuals = sorted(
            (
                asset
                for asset in request.assets
                if asset.artifact_type in {ArtifactType.IMAGE, ArtifactType.VIDEO_CLIP}
            ),
            key=lambda asset: int(asset.metadata["scene_order"]),
        )
        audio = self._one_asset(request, ArtifactType.VOICE)
        subtitles = self._one_asset(request, ArtifactType.SUBTITLE)
        if len(visuals) != len(request.script.scenes):
            raise ValueError("Renderer requires exactly one visual for each script scene")

        command = [str(self.executable), "-hide_banner", "-loglevel", "error", "-y"]
        for visual, scene in zip(visuals, request.script.scenes, strict=True):
            if visual.artifact_type == ArtifactType.IMAGE:
                command.extend(["-loop", "1"])
            else:
                command.extend(["-stream_loop", "-1"])
            command.extend(
                [
                    "-t",
                    str(scene.duration_seconds),
                    "-i",
                    str(self.storage_root / visual.relative_path),
                ]
            )
        presenter_inputs = _presenter_inputs_by_scene(request.character_assets)
        presenter_input_indexes: dict[int, int] = {}
        for scene_order, presenter in presenter_inputs.items():
            presenter_input_indexes[scene_order] = len(visuals) + len(presenter_input_indexes)
            command.extend(
                [
                    "-loop",
                    "1",
                    "-t",
                    str(_scene_duration(request, scene_order)),
                    "-i",
                    str(presenter.asset_path),
                ]
            )
        command.extend(["-i", str(self.storage_root / audio.relative_path)])

        video_chains = []
        concat_inputs = []
        for index, scene in enumerate(request.script.scenes):
            scene_label = f"v{index}"
            video_chains.append(
                f"[{index}:v]scale={request.template.width}:{request.template.height}:"
                "force_original_aspect_ratio=increase,"
                f"crop={request.template.width}:{request.template.height},"
                f"setsar=1,fps={request.template.frames_per_second},"
                f"trim=duration={scene.duration_seconds},setpts=PTS-STARTPTS[bg{index}]"
            )
            presenter = presenter_inputs.get(scene.order)
            if presenter is not None:
                presenter_index = presenter_input_indexes[scene.order]
                presenter_label = f"p{index}"
                height = max(1, int(request.template.height * presenter.scale))
                fade_start = max(0, scene.duration_seconds - self.presenter_layout.fade_seconds)
                fade_filters = ""
                if presenter.entrance == "fade":
                    fade_filters += (
                        f",fade=t=in:st=0:d={self.presenter_layout.fade_seconds}:alpha=1"
                    )
                if presenter.exit == "fade":
                    fade_filters += (
                        f",fade=t=out:st={fade_start}:d={self.presenter_layout.fade_seconds}:alpha=1"
                    )
                video_chains.append(
                    f"[{presenter_index}:v]format=rgba,scale=-1:{height},"
                    f"fps={request.template.frames_per_second},"
                    f"trim=duration={scene.duration_seconds},setpts=PTS-STARTPTS"
                    f"{fade_filters}[{presenter_label}]"
                )
                x, y = self._presenter_position(presenter)
                video_chains.append(
                    f"[bg{index}][{presenter_label}]overlay=x={x}:y={y}:format=auto[{scene_label}]"
                )
            else:
                video_chains.append(f"[bg{index}]copy[{scene_label}]")
            concat_inputs.append(f"[{scene_label}]")
        subtitle_path = self.storage_root / subtitles.relative_path
        escaped_subtitle_path = _escape_filter_path(subtitle_path)
        filter_complex = ";".join(video_chains)
        filter_complex += (
            f";{''.join(concat_inputs)}concat=n={len(visuals)}:v=1:a=0[base]"
            f";[base]subtitles='{escaped_subtitle_path}':"
            "force_style='Alignment=2,FontSize=28,MarginV=150,Outline=2,Shadow=0'[video]"
        )
        command.extend(
            [
                "-filter_complex",
                filter_complex,
                "-map",
                "[video]",
                "-map",
                f"{len(visuals) + len(presenter_inputs)}:a:0",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(request.template.frames_per_second),
                "-c:a",
                "aac",
                "-shortest",
                str(output),
            ]
        )
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed: {completed.stderr.strip()}")
        return RenderResult(
            render=GeneratedAsset(
                artifact_type=ArtifactType.RENDER,
                relative_path=Path(output.name),
                media_type="video/mp4",
                metadata={"template": request.template.name},
            ),
            duration_seconds=request.script.duration_seconds,
        )

    def _presenter_position(self, presenter: CharacterAssetReference) -> tuple[str, str]:
        y = f"H-h-{self.presenter_layout.subtitle_safe_bottom}"
        if presenter.position == "bottom_left":
            return str(self.presenter_layout.margin_x), y
        if presenter.position == "bottom_center":
            return "(W-w)/2", y
        return f"W-w-{self.presenter_layout.margin_x}", y

    def _require_executable(self) -> None:
        if not self.executable.is_file():
            raise MissingMediaExecutable(f"FFmpeg executable not found: {self.executable}")

    @staticmethod
    def _one_asset(request: RenderRequest, artifact_type: ArtifactType) -> GeneratedAsset:
        matches = [asset for asset in request.assets if asset.artifact_type == artifact_type]
        if len(matches) != 1:
            raise ValueError(f"Renderer requires exactly one {artifact_type} asset")
        return matches[0]


class FfprobeValidator:
    def __init__(self, executable: Path) -> None:
        self.executable = executable

    def validate(
        self, render: Path, expected_duration_seconds: float | None = None
    ) -> ValidationReport:
        if not self.executable.is_file():
            raise MissingMediaExecutable(f"ffprobe executable not found: {self.executable}")
        command = [
            str(self.executable),
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(render),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"ffprobe validation failed: {completed.stderr.strip()}")
        payload = json.loads(completed.stdout)
        streams = payload.get("streams", [])
        video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
        audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
        duration = float(payload.get("format", {}).get("duration", 0))
        checks = (
            ValidationCheck(name="file_exists", passed=render.is_file()),
            ValidationCheck(name="video_stream", passed=video is not None),
            ValidationCheck(name="audio_stream", passed=audio is not None),
            ValidationCheck(
                name="video_codec",
                passed=bool(video and video.get("codec_name") == "h264"),
                detail=video.get("codec_name", "missing") if video else "missing",
            ),
            ValidationCheck(
                name="audio_codec",
                passed=bool(audio and audio.get("codec_name") == "aac"),
                detail=audio.get("codec_name", "missing") if audio else "missing",
            ),
            ValidationCheck(
                name="resolution",
                passed=bool(video and video.get("width") == 1080 and video.get("height") == 1920),
                detail=f"{video.get('width')}x{video.get('height')}" if video else "missing",
            ),
            ValidationCheck(
                name="frame_rate",
                passed=bool(video and _frame_rate(video.get("avg_frame_rate", "0/1")) == 30),
                detail=video.get("avg_frame_rate", "missing") if video else "missing",
            ),
            ValidationCheck(
                name="duration",
                passed=(
                    duration > 0
                    and (
                        expected_duration_seconds is None
                        or abs(duration - expected_duration_seconds) <= 0.15
                    )
                ),
                detail=(
                    f"observed={duration}; expected={expected_duration_seconds}"
                    if expected_duration_seconds is not None
                    else str(duration)
                ),
            ),
        )
        return ValidationReport(
            checks=checks,
            passed=all(check.passed or not check.blocking for check in checks),
        )


def _escape_filter_path(path: Path) -> str:
    return path.as_posix().replace(":", r"\:").replace("'", r"\'")


def _presenter_inputs_by_scene(
    presenters: tuple[CharacterAssetReference, ...],
) -> dict[int, CharacterAssetReference]:
    return {presenter.scene_order: presenter for presenter in presenters}


def _scene_duration(request: RenderRequest, scene_order: int) -> float:
    return next(
        scene.duration_seconds for scene in request.script.scenes if scene.order == scene_order
    )


def _frame_rate(value: str) -> float:
    numerator, denominator = value.split("/", maxsplit=1)
    return float(numerator) / float(denominator)
