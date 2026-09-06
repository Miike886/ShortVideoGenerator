import argparse
import json
from pathlib import Path

from short_video_generator.bootstrap import build_manual_pipeline, default_idempotency_key
from short_video_generator.config import Settings
from short_video_generator.contracts import ManualProductionInput
from short_video_generator.providers.assets import FakeAssetProvider

BYTE_VOICE_REFERENCES = {
    "en": (
        "Okay, this is actually pretty strange. Microsoft says its new AI system can process "
        "information much faster than before. But here's the interesting part: it doesn't just "
        "analyze text — it can work with images, audio, and video too. So... is this actually a "
        "big deal? Well, yes and no. And the reason why is surprisingly simple."
    ),
    "es": (
        "Esto es bastante más extraño de lo que parece. Microsoft presentó un nuevo sistema de "
        "inteligencia artificial capaz de trabajar con texto, imágenes, audio y video. Pero aquí "
        "viene lo interesante: también puede conectarse con herramientas como GitHub y ejecutar "
        "ciertas tareas automáticamente. Entonces... ¿realmente cambia algo? Sí, pero no "
        "exactamente por la razón que imaginas."
    ),
}


def run() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic local vertical slice")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--topic", default="How does a local video pipeline work?")
    parser.add_argument("--language", default="en")
    parser.add_argument("--target-duration-seconds", type=int)
    parser.add_argument("--idempotency-key")
    parser.add_argument("--ffmpeg", type=Path)
    parser.add_argument("--ffprobe", type=Path)
    parser.add_argument("--tts-provider", choices=("fake", "edge", "elevenlabs"))
    parser.add_argument("--tts-mode", choices=("live", "cached"))
    parser.add_argument("--byte-voice-stress-test", action="store_true")
    parser.add_argument("--tts-voice")
    parser.add_argument("--tts-rate", type=int)
    parser.add_argument("--tts-volume", type=int)
    parser.add_argument("--asset-provider", choices=("fake", "pexels"))
    parser.add_argument("--caption-alignment-provider", choices=("fake", "whisperx"))
    parser.add_argument("--default-character-id")
    arguments = parser.parse_args()

    discovered = Settings.local(arguments.project_root)
    settings = Settings(
        project_root=discovered.project_root,
        database_path=discovered.database_path,
        storage_root=discovered.storage_root,
        ffmpeg_path=arguments.ffmpeg or discovered.ffmpeg_path,
        ffprobe_path=arguments.ffprobe or discovered.ffprobe_path,
        tts_provider=arguments.tts_provider or discovered.tts_provider,
        tts_mode=arguments.tts_mode or discovered.tts_mode,
        tts_voice=arguments.tts_voice or discovered.tts_voice,
        tts_rate=(
            arguments.tts_rate
            if arguments.tts_rate is not None
            else discovered.tts_rate
        ),
        tts_volume=(
            arguments.tts_volume
            if arguments.tts_volume is not None
            else discovered.tts_volume
        ),
        elevenlabs_api_key=discovered.elevenlabs_api_key,
        elevenlabs_voice_id=discovered.elevenlabs_voice_id,
        elevenlabs_voice_version=discovered.elevenlabs_voice_version,
        elevenlabs_model_id=discovered.elevenlabs_model_id,
        elevenlabs_stability=discovered.elevenlabs_stability,
        elevenlabs_similarity_boost=discovered.elevenlabs_similarity_boost,
        elevenlabs_style=discovered.elevenlabs_style,
        elevenlabs_use_speaker_boost=discovered.elevenlabs_use_speaker_boost,
        elevenlabs_speed=discovered.elevenlabs_speed,
        asset_provider=arguments.asset_provider or discovered.asset_provider,
        pexels_api_key=discovered.pexels_api_key,
        default_character_id=arguments.default_character_id or discovered.default_character_id,
        caption_alignment_provider=(
            arguments.caption_alignment_provider
            or discovered.caption_alignment_provider
        ),
        whisperx_model=discovered.whisperx_model,
        whisperx_device=discovered.whisperx_device,
    )
    if arguments.byte_voice_stress_test:
        if settings.tts_provider != "elevenlabs":
            raise ValueError("--byte-voice-stress-test requires TTS_PROVIDER=elevenlabs")
        results = []
        for language, text in BYTE_VOICE_REFERENCES.items():
            reference_pipeline = build_manual_pipeline(
                settings,
                ManualProductionInput(
                    topic=f"Byte Voice v1 {language} reference",
                    language=language,
                ),
                asset_provider=FakeAssetProvider(),
            )
            result = reference_pipeline.execute_tts_reference(
                f"byte-voice-v1-{language}-reference", text
            )
            results.append(
                {
                    "language": language,
                    "reused": result.reused,
                    "artifact_path": result.artifact.relative_path.as_posix(),
                    "metadata": result.artifact.metadata,
                }
            )
        print(json.dumps(results, indent=2))
        return
    production_input = ManualProductionInput(
        topic=arguments.topic,
        language=arguments.language,
        target_duration_seconds=arguments.target_duration_seconds,
    )
    idempotency_key = arguments.idempotency_key or default_idempotency_key(
        production_input, settings
    )
    result = build_manual_pipeline(settings, production_input).execute(idempotency_key)
    print(
        json.dumps(
            {
                "idempotency_key": idempotency_key,
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
