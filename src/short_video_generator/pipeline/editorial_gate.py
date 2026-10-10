import hashlib
import json
from dataclasses import dataclass

from short_video_generator.contracts import VideoScript


@dataclass(frozen=True, slots=True)
class EditorialGateResult:
    passed: bool
    warnings: tuple[str, ...] = ()


class EditorialGateError(ValueError):
    pass


class EditorialGate:
    version = "editorial-gate-v1"

    def fingerprint(self, script: VideoScript) -> str:
        payload = {
            "version": self.version,
            "story_plan": script.story_plan.model_dump(mode="json") if script.story_plan else None,
            "script": script.model_dump(mode="json", exclude={"story_plan"}),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def validate(self, script: VideoScript) -> EditorialGateResult:
        plan = script.story_plan
        if plan is None:
            raise EditorialGateError("EditorialGate requires a SemanticStoryPlan")
        warnings = list(plan.validate_progression())
        if len(plan.scenes) != len(script.scenes):
            warnings.append("story plan and renderable script scene counts differ")
        if any(not scene.visual_concept.subject.strip() for scene in plan.scenes):
            warnings.append("every scene must have a visual subject")
        if warnings:
            raise EditorialGateError("EditorialGate rejected story: " + "; ".join(warnings))
        return EditorialGateResult(passed=True)
