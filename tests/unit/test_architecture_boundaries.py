import ast
from pathlib import Path


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }


def test_domain_has_no_framework_or_infrastructure_dependencies() -> None:
    domain = Path("src/short_video_generator/domain")
    forbidden = {"fastapi", "pydantic", "sqlalchemy", "subprocess"}
    for module in domain.glob("*.py"):
        assert imported_roots(module).isdisjoint(forbidden), module


def test_provider_ports_do_not_depend_on_implementations() -> None:
    ports = Path("src/short_video_generator/providers/ports.py")
    assert "deterministic" not in ports.read_text(encoding="utf-8")


def test_pipeline_has_no_framework_persistence_or_concrete_adapter_dependencies() -> None:
    pipeline = Path("src/short_video_generator/pipeline")
    forbidden_roots = {"fastapi", "sqlalchemy", "subprocess"}
    forbidden_modules = (
        "short_video_generator.persistence",
        "short_video_generator.rendering",
        "short_video_generator.storage",
        "short_video_generator.providers.deterministic",
        "short_video_generator.providers.evaluation",
    )
    for module in pipeline.glob("*.py"):
        imports = imported_modules(module)
        assert imported_roots(module).isdisjoint(forbidden_roots), module
        assert not any(
            imported.startswith(prefix) for imported in imports for prefix in forbidden_modules
        ), module
