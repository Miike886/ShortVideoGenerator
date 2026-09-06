from enum import StrEnum


class RunTrigger(StrEnum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CandidateStatus(StrEnum):
    DISCOVERED = "discovered"
    EVALUATED = "evaluated"
    SELECTED = "selected"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class ProductionStatus(StrEnum):
    SELECTED = "selected"
    BRIEF_READY = "brief_ready"
    SCRIPT_READY = "script_ready"
    ASSETS_READY = "assets_ready"
    RENDERED = "rendered"
    VALIDATING = "validating"
    VALIDATION_FAILED = "validation_failed"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    FAILED = "failed"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ArtifactType(StrEnum):
    SOURCE_SNAPSHOT = "source_snapshot"
    VOICE = "voice"
    TIMELINE = "timeline"
    CHARACTER_REFERENCE = "character_reference"
    IMAGE = "image"
    VIDEO_CLIP = "video_clip"
    SUBTITLE = "subtitle"
    RENDER = "render"
    THUMBNAIL = "thumbnail"
    VALIDATION_REPORT = "validation_report"
