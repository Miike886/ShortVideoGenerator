import argparse
import json
from pathlib import Path

from short_video_generator.bootstrap import build_manual_pipeline
from short_video_generator.config import Settings


def run() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic local vertical slice")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--idempotency-key", default="manual-fixture-v1")
    parser.add_argument("--ffmpeg", type=Path)
    parser.add_argument("--ffprobe", type=Path)
    arguments = parser.parse_args()

    discovered = Settings.local(arguments.project_root)
    settings = Settings(
        project_root=discovered.project_root,
        database_path=discovered.database_path,
        storage_root=discovered.storage_root,
        ffmpeg_path=arguments.ffmpeg or discovered.ffmpeg_path,
        ffprobe_path=arguments.ffprobe or discovered.ffprobe_path,
    )
    result = build_manual_pipeline(settings).execute(arguments.idempotency_key)
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "production_id": result.production_id,
                "status": result.status,
                "reused": result.reused,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    run()
