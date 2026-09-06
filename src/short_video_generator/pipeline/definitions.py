from enum import StrEnum


class PipelineStep(StrEnum):
    DISCOVER = "discover"
    EVALUATE = "evaluate"
    SELECT = "select"
    CREATE_BRIEF = "create_brief"
    CREATE_SCRIPT = "create_script"
    GENERATE_ASSETS = "generate_assets"
    RENDER = "render"
    VALIDATE = "validate"
    ENQUEUE_REVIEW = "enqueue_review"


VERTICAL_SLICE_STEPS: tuple[PipelineStep, ...] = tuple(PipelineStep)
