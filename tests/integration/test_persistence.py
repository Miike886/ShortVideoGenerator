from sqlalchemy import inspect

from short_video_generator.config import Settings
from short_video_generator.persistence.database import build_engine, create_schema


def test_sqlite_schema_contains_vertical_slice_entities(tmp_path) -> None:
    settings = Settings.local(tmp_path)
    engine = build_engine(settings)
    create_schema(engine)

    tables = set(inspect(engine).get_table_names())
    assert {
        "niches",
        "source_configs",
        "pipeline_runs",
        "step_runs",
        "topic_candidates",
        "productions",
        "artifacts",
        "reviews",
    } <= tables
