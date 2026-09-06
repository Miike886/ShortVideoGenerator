from enum import StrEnum


class PipelineStep(StrEnum):
    DISCOVER = "discover"
    EVALUATE = "evaluate"
    SELECT = "select"
    CREATE_BRIEF = "create_brief"
    CREATE_SCRIPT = "create_script"
    GENERATE_AUDIO = "generate_audio"
    PLAN_TIMELINE = "plan_timeline"
    RESOLVE_PRESENTERS = "resolve_presenters"
    GENERATE_ASSETS = "generate_assets"
    GENERATE_SUBTITLES = "generate_subtitles"
    RENDER = "render"
    VALIDATE = "validate"
    ENQUEUE_REVIEW = "enqueue_review"


VERTICAL_SLICE_STEPS: tuple[PipelineStep, ...] = tuple(PipelineStep)
