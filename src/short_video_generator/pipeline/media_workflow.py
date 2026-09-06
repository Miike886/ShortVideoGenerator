import hashlib
import json
from pathlib import Path

from short_video_generator.contracts import (
    CharacterAssetReference,
    GeneratedAsset,
    PresenterInstruction,
    RenderRequest,
    TextToSpeechOptions,
    VideoScript,
    WordTiming,
)
from short_video_generator.domain.enums import ArtifactType, ProductionStatus
from short_video_generator.domain.transitions import require_transition
from short_video_generator.pipeline.definitions import PipelineStep
from short_video_generator.pipeline.models import (
    ArtifactState,
    ExecutionState,
    ProductionState,
    StoredFile,
)
from short_video_generator.pipeline.ports import ArtifactStore, AudioProbe, SubtitleProvider
from short_video_generator.pipeline.steps import StepExecutor
from short_video_generator.pipeline.timeline import fit_script_to_audio
from short_video_generator.providers.ports import (
    AssetProvider,
    CaptionAlignmentProvider,
    CharacterAssetProvider,
    Renderer,
    TextToSpeechProvider,
)


class NarratedMediaWorkflow:
    timeline_version = "word-weighted-v1"
    presenter_version = "deterministic-presenter-v1"

    def __init__(
        self,
        steps: StepExecutor,
        store: ArtifactStore,
        speech: TextToSpeechProvider,
        speech_options: TextToSpeechOptions,
        language: str,
        audio_probe: AudioProbe,
        assets: AssetProvider,
        caption_alignment: CaptionAlignmentProvider,
        characters: CharacterAssetProvider,
        default_character_id: str,
        subtitles: SubtitleProvider,
        renderer: Renderer,
    ) -> None:
        self.steps = steps
        self.store = store
        self.speech = speech
        self.speech_options = speech_options
        self.language = language
        self.audio_probe = audio_probe
        self.assets = assets
        self.caption_alignment = caption_alignment
        self.characters = characters
        self.default_character_id = default_character_id
        self.subtitles = subtitles
        self.renderer = renderer

    def render(self, execution: ExecutionState, production: ProductionState, work: Path) -> Path:
        audio = self._generate_audio(execution, production, work)
        self._plan_timeline(execution, production, audio, work)
        self._resolve_presenters(execution, production, work)
        self._generate_visuals(execution, production, work)
        alignment = self._align_captions(execution, production, audio, work)
        self._generate_subtitles(execution, production, alignment, work)
        return self._render_video(execution, production, work)

    def _generate_audio(
        self, execution: ExecutionState, production: ProductionState, work: Path
    ) -> ArtifactState:
        script = VideoScript.model_validate(production.script)
        text = " ".join(scene.narration for scene in script.scenes)
        fingerprint = _fingerprint(
            {
                "text": text,
                "options": self.speech_options.model_dump(mode="json"),
                "provider": self.speech.provider_name,
                "provider_version": self.speech.provider_version,
                "language": self.language,
            }
        )
        artifact = _artifact(execution, ArtifactType.VOICE)
        if (
            artifact is not None
            and artifact.metadata.get("input_fingerprint") == fingerprint
            and self.steps.completed(
                execution, PipelineStep.GENERATE_AUDIO, production.id, fingerprint
            )
        ):
            return artifact

        def action() -> ArtifactState:
            output = work / f"voice{self.speech.output_suffix}"
            generated = self.speech.synthesize(
                text, output, self.language, self.speech_options
            )
            observed = self.audio_probe.inspect(output)
            stored = self.store.promote(
                output, self.store.asset_directory(production.id) / output.name
            )
            metadata = generated.model_dump(mode="json") | observed.model_dump(mode="json")
            metadata["input_fingerprint"] = fingerprint
            return _upsert_artifact(
                execution,
                ArtifactType.VOICE,
                self.speech.output_media_type,
                metadata,
                stored,
            )

        return self.steps.run(
            execution,
            PipelineStep.GENERATE_AUDIO,
            production.id,
            action,
            fingerprint,
        )

    def _resolve_presenters(
        self, execution: ExecutionState, production: ProductionState, work: Path
    ) -> None:
        script = VideoScript.model_validate(production.script)
        presenter_assets = self._presenter_assets(script)
        fingerprint = _fingerprint(
            {
                "provider": self.characters.provider_name,
                "provider_version": self.characters.provider_version,
                "planner": self.presenter_version,
                "presenters": [
                    asset.model_dump(mode="json", exclude={"asset_path"})
                    for asset in presenter_assets
                ],
            }
        )
        artifact = _artifact(execution, ArtifactType.CHARACTER_REFERENCE)
        if (
            artifact is not None
            and artifact.metadata.get("input_fingerprint") == fingerprint
            and self.steps.completed(
                execution, PipelineStep.RESOLVE_PRESENTERS, production.id, fingerprint
            )
        ):
            return

        def action() -> None:
            payload = {
                "planner": self.presenter_version,
                "presenters": [
                    asset.model_dump(mode="json", exclude={"asset_path"})
                    for asset in presenter_assets
                ],
            }
            reference_path = self.store.write_text(
                work, "presenters.json", json.dumps(payload, indent=2, sort_keys=True)
            )
            stored = self.store.promote(
                reference_path,
                self.store.asset_directory(production.id) / reference_path.name,
            )
            _upsert_artifact(
                execution,
                ArtifactType.CHARACTER_REFERENCE,
                "application/json",
                payload | {"input_fingerprint": fingerprint},
                stored,
            )

        self.steps.run(
            execution,
            PipelineStep.RESOLVE_PRESENTERS,
            production.id,
            action,
            fingerprint,
        )

    def _plan_timeline(
        self,
        execution: ExecutionState,
        production: ProductionState,
        audio: ArtifactState,
        work: Path,
    ) -> None:
        duration = float(audio.metadata["duration_seconds"])
        fingerprint = _fingerprint(
            {
                "audio_sha256": audio.sha256,
                "duration_seconds": duration,
                "planner": self.timeline_version,
            }
        )
        timeline = _artifact(execution, ArtifactType.TIMELINE)
        if (
            timeline is not None
            and timeline.metadata.get("input_fingerprint") == fingerprint
            and self.steps.completed(
                execution, PipelineStep.PLAN_TIMELINE, production.id, fingerprint
            )
        ):
            return

        def action() -> None:
            script = fit_script_to_audio(VideoScript.model_validate(production.script), duration)
            production.script = script.model_dump(mode="json")
            timeline_path = self.store.write_text(
                work, "timeline.json", script.model_dump_json(indent=2)
            )
            stored = self.store.promote(
                timeline_path,
                self.store.asset_directory(production.id) / timeline_path.name,
            )
            _upsert_artifact(
                execution,
                ArtifactType.TIMELINE,
                "application/json",
                {
                    "duration_seconds": duration,
                    "planner": self.timeline_version,
                    "input_fingerprint": fingerprint,
                },
                stored,
            )

        self.steps.run(
            execution,
            PipelineStep.PLAN_TIMELINE,
            production.id,
            action,
            fingerprint,
        )

    def _generate_visuals(
        self, execution: ExecutionState, production: ProductionState, work: Path
    ) -> None:
        script = VideoScript.model_validate(production.script)
        scene_fingerprints = {
            scene.order: _fingerprint(
                {
                    "visual_query": scene.visual_query or scene.narration,
                    "provider": self.assets.provider_name,
                    "provider_version": self.assets.provider_version,
                    "selection_strategy": self.assets.selection_strategy_version,
                }
            )
            for scene in script.scenes
        }
        fingerprint = _fingerprint(
            {"scene_fingerprints": scene_fingerprints, "scene_count": len(script.scenes)}
        )
        visuals = [
            item
            for item in execution.artifacts
            if item.artifact_type in {ArtifactType.IMAGE, ArtifactType.VIDEO_CLIP}
        ]
        if (
            len(visuals) == len(script.scenes)
            and all(
                item.metadata.get("input_fingerprint")
                == scene_fingerprints[int(item.metadata["scene_order"])]
                for item in visuals
            )
            and self.steps.completed(
                execution, PipelineStep.GENERATE_ASSETS, production.id, fingerprint
            )
        ):
            return

        def action() -> None:
            for scene in script.scenes:
                scene_fingerprint = scene_fingerprints[scene.order]
                existing = next(
                    (
                        item
                        for item in visuals
                        if item.metadata.get("scene_order") == scene.order
                        and item.metadata.get("input_fingerprint") == scene_fingerprint
                    ),
                    None,
                )
                if existing is not None:
                    continue
                draft = self.assets.acquire(
                    scene.visual_query or scene.narration,
                    scene.order,
                    work,
                )
                stored = self.store.promote(
                    work / draft.relative_path,
                    self.store.asset_directory(production.id) / draft.relative_path.name,
                )
                _upsert_artifact(
                    execution,
                    draft.artifact_type,
                    draft.media_type,
                    draft.metadata
                    | {
                        "scene_order": scene.order,
                        "input_fingerprint": scene_fingerprint,
                    },
                    stored,
                )

        self.steps.run(
            execution,
            PipelineStep.GENERATE_ASSETS,
            production.id,
            action,
            fingerprint,
        )

    def _generate_subtitles(
        self,
        execution: ExecutionState,
        production: ProductionState,
        alignment: ArtifactState,
        work: Path,
    ) -> None:
        script = VideoScript.model_validate(production.script)
        words = _word_timings(alignment)
        fingerprint = _fingerprint(
            {
                "alignment_sha256": alignment.sha256,
                "words": [word.model_dump(mode="json") for word in words],
                "provider": self.subtitles.provider_name,
                "provider_version": self.subtitles.provider_version,
            }
        )
        subtitle = _artifact(execution, ArtifactType.SUBTITLE)
        if (
            subtitle is not None
            and subtitle.metadata.get("input_fingerprint") == fingerprint
            and self.steps.completed(
                execution, PipelineStep.GENERATE_SUBTITLES, production.id, fingerprint
            )
        ):
            return

        def action() -> None:
            draft = self.subtitles.create(script, words, work)
            stored = self.store.promote(
                work / draft.relative_path,
                self.store.asset_directory(production.id) / draft.relative_path.name,
            )
            _upsert_artifact(
                execution,
                ArtifactType.SUBTITLE,
                draft.media_type,
                draft.metadata | {"input_fingerprint": fingerprint},
                stored,
            )
            _transition(production, ProductionStatus.ASSETS_READY, PipelineStep.GENERATE_SUBTITLES)

        self.steps.run(
            execution,
            PipelineStep.GENERATE_SUBTITLES,
            production.id,
            action,
            fingerprint,
        )

    def _align_captions(
        self,
        execution: ExecutionState,
        production: ProductionState,
        audio: ArtifactState,
        work: Path,
    ) -> ArtifactState:
        script = VideoScript.model_validate(production.script)
        audio_path = self.store.resolve(audio.relative_path)
        text = " ".join(scene.narration for scene in script.scenes)
        fingerprint = _fingerprint(
            {
                "audio_sha256": audio.sha256,
                "text": text,
                "provider": self.caption_alignment.provider_name,
                "provider_version": self.caption_alignment.provider_version,
            }
        )
        alignment = _artifact(execution, ArtifactType.CAPTION_ALIGNMENT)
        if (
            alignment is not None
            and alignment.metadata.get("input_fingerprint") == fingerprint
            and self.steps.completed(
                execution, PipelineStep.ALIGN_CAPTIONS, production.id, fingerprint
            )
        ):
            return alignment

        def action() -> ArtifactState:
            result = self.caption_alignment.align(
                audio_path, script, float(audio.metadata["duration_seconds"])
            )
            alignment_path = self.store.write_text(
                work, "alignment.json", result.model_dump_json(indent=2)
            )
            stored = self.store.promote(
                alignment_path,
                self.store.asset_directory(production.id) / alignment_path.name,
            )
            return _upsert_artifact(
                execution,
                ArtifactType.CAPTION_ALIGNMENT,
                "application/json",
                result.model_dump(mode="json")
                | {
                    "input_fingerprint": fingerprint,
                    "word_count": len(result.words),
                },
                stored,
            )

        return self.steps.run(
            execution,
            PipelineStep.ALIGN_CAPTIONS,
            production.id,
            action,
            fingerprint,
        )

    def _render_video(
        self, execution: ExecutionState, production: ProductionState, work: Path
    ) -> Path:
        render = _artifact(execution, ArtifactType.RENDER)
        render_fingerprint = _fingerprint(
            {
                "script": production.script,
                "artifacts": [
                    {
                        "type": item.artifact_type,
                        "path": item.relative_path.as_posix(),
                        "sha256": item.sha256,
                        "metadata": item.metadata,
                    }
                    for item in execution.artifacts
                    if item.artifact_type != ArtifactType.RENDER
                ],
                "renderer": "ffmpeg-presenter-ass-v1",
            }
        )
        if render is not None and render.metadata.get("input_fingerprint") == render_fingerprint:
            return self.store.resolve(render.relative_path)

        def action() -> Path:
            script = VideoScript.model_validate(production.script)
            result = self.renderer.render(
                RenderRequest(
                    production_id=production.id,
                    script=script,
                    assets=tuple(_artifact_contracts(execution)),
                    character_assets=tuple(self._presenter_assets(script)),
                ),
                work,
            )
            stored = self.store.promote(
                work / result.render.relative_path,
                self.store.render_directory(production.id) / "final.mp4",
            )
            _upsert_artifact(
                execution,
                ArtifactType.RENDER,
                "video/mp4",
                result.render.metadata
                | {
                    "duration_seconds": result.duration_seconds,
                    "input_fingerprint": render_fingerprint,
                },
                stored,
            )
            _transition(production, ProductionStatus.RENDERED, PipelineStep.RENDER)
            return stored.absolute_path

        return self.steps.run(execution, PipelineStep.RENDER, production.id, action)

    def _presenter_assets(self, script: VideoScript) -> list[CharacterAssetReference]:
        return [
            self.characters.resolve(
                scene.presenter
                or _default_presenter_instruction(scene.role, self.default_character_id),
                scene.order,
            )
            for scene in script.scenes
            if scene.presenter is None or scene.presenter.visibility
        ]


def _fingerprint(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _artifact(execution: ExecutionState, artifact_type: ArtifactType) -> ArtifactState | None:
    return next(
        (item for item in execution.artifacts if item.artifact_type == artifact_type),
        None,
    )


def _artifact_contracts(execution: ExecutionState) -> list[GeneratedAsset]:
    return [
        GeneratedAsset(
            artifact_type=item.artifact_type,
            relative_path=item.relative_path,
            media_type=item.mime_type,
            metadata=item.metadata,
        )
        for item in execution.artifacts
    ]


def _word_timings(alignment: ArtifactState) -> tuple[WordTiming, ...]:
    words = alignment.metadata.get("words")
    if not isinstance(words, list):
        raise ValueError("Caption alignment artifact is missing word timings")
    return tuple(WordTiming.model_validate(word) for word in words)


def _default_presenter_instruction(role: str, character_id: str) -> PresenterInstruction:
    role_map = {
        "hook": ("explaining", "bottom_right", 0.32),
        "context": ("thinking", "bottom_left", 0.3),
        "fact": ("surprised", "bottom_right", 0.32),
        "development": ("pointing_left", "bottom_right", 0.3),
        "payoff": ("skeptical", "bottom_left", 0.3),
        "conclusion": ("happy", "bottom_left", 0.3),
    }
    pose, position, scale = role_map.get(role, role_map["fact"])
    return PresenterInstruction(
        character_id=character_id,
        pose=pose,
        position=position,
        scale=scale,
    )


def _upsert_artifact(
    execution: ExecutionState,
    artifact_type: ArtifactType,
    media_type: str,
    metadata: dict[str, object],
    stored: StoredFile,
) -> ArtifactState:
    existing = next(
        (
            item
            for item in execution.artifacts
            if item.relative_path == stored.relative_path
            or (
                artifact_type
                in {
                    ArtifactType.CHARACTER_REFERENCE,
                    ArtifactType.IMAGE,
                    ArtifactType.VIDEO_CLIP,
                }
                and item.artifact_type in {ArtifactType.IMAGE, ArtifactType.VIDEO_CLIP}
                and item.metadata.get("scene_order") == metadata.get("scene_order")
            )
        ),
        None,
    )
    if existing is None:
        existing = ArtifactState(
            artifact_type=artifact_type,
            relative_path=stored.relative_path,
        )
        execution.artifacts.append(existing)
    existing.artifact_type = artifact_type
    existing.mime_type = media_type
    existing.size_bytes = stored.size_bytes
    existing.sha256 = stored.sha256
    existing.metadata = metadata
    return existing


def _transition(production: ProductionState, target: ProductionStatus, step: PipelineStep) -> None:
    require_transition(production.status, target)
    production.status = target
    production.current_step = step
