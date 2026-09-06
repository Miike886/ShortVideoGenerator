import json
import subprocess
from pathlib import Path

from short_video_generator.contracts import AudioProbeResult

from .ffmpeg import MissingMediaExecutable


class FfprobeAudioProbe:
    def __init__(self, executable: Path) -> None:
        self.executable = executable

    def inspect(self, audio: Path) -> AudioProbeResult:
        if not self.executable.is_file():
            raise MissingMediaExecutable(f"ffprobe executable not found: {self.executable}")
        command = [
            str(self.executable),
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,sample_rate:format=duration",
            "-of",
            "json",
            str(audio),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"ffprobe audio inspection failed: {completed.stderr.strip()}")
        payload = json.loads(completed.stdout)
        streams = payload.get("streams", [])
        if len(streams) != 1:
            raise ValueError("Audio artifact must contain exactly one audio stream")
        stream = streams[0]
        return AudioProbeResult(
            duration_seconds=float(payload.get("format", {}).get("duration", 0)),
            codec_name=stream.get("codec_name", "unknown"),
            sample_rate=(int(stream["sample_rate"]) if stream.get("sample_rate") else None),
        )
