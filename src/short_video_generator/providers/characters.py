import hashlib
from pathlib import Path

from short_video_generator.contracts import (
    CharacterAssetReference,
    CharacterDefinition,
    PresenterInstruction,
)

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class LocalCharacterAssetProvider:
    provider_name = "local-character-assets"
    provider_version = "character-yaml-v1"

    def __init__(self, character_root: Path) -> None:
        self.character_root = character_root.resolve()

    def resolve(
        self, instruction: PresenterInstruction, scene_order: int
    ) -> CharacterAssetReference:
        definition_path = self.character_root / instruction.character_id / "character.yaml"
        definition = self._load_definition(definition_path)
        pose = instruction.pose
        fallback_reason = None
        if pose not in definition.available_poses:
            fallback_reason = f"Pose {pose!r} is not available; used default pose"
            pose = definition.default_pose
        self._validate_required_poses(definition, definition_path.parent)
        asset_relative_path = (
            Path("assets")
            / "characters"
            / definition.id
            / definition.asset_directory
            / f"{pose}.png"
        )
        asset_path = (
            definition_path.parent / definition.asset_directory / f"{pose}.png"
        ).resolve()
        width, height, has_alpha = _inspect_png(asset_path)
        if not has_alpha:
            raise ValueError(f"Character pose must be transparent PNG/RGBA: {asset_path}")
        position = instruction.position or definition.preferred_screen_position
        scale = instruction.scale if instruction.scale is not None else definition.scale
        fingerprint = _fingerprint(
            {
                "provider": self.provider_name,
                "provider_version": self.provider_version,
                "character_id": definition.id,
                "character_version": definition.version,
                "pose": pose,
                "requested_pose": instruction.pose,
                "fallback_reason": fallback_reason,
                "definition_sha256": _sha256(definition_path),
                "asset_sha256": _sha256(asset_path),
                "position": position,
                "scale": scale,
                "entrance": instruction.entrance,
                "exit": instruction.exit,
                "action": getattr(instruction, "action", "idle"),
                "facing": getattr(instruction, "facing", "viewer"),
                "motion_preset": getattr(instruction, "motion_preset", "byte_idle_hover"),
                "beats": getattr(instruction, "beats", ()),
            }
        )
        return CharacterAssetReference(
            scene_order=scene_order,
            character_id=definition.id,
            character_name=definition.name,
            character_version=definition.version,
            pose=pose,
            requested_pose=instruction.pose,
            fallback_reason=fallback_reason,
            asset_path=asset_path,
            asset_relative_path=asset_relative_path,
            width=width,
            height=height,
            has_alpha=has_alpha,
            position=position,
            scale=scale,
            entrance=instruction.entrance,
            exit=instruction.exit,
            action=getattr(instruction, "action", "idle"),
            facing=getattr(instruction, "facing", "viewer"),
            motion_preset=getattr(instruction, "motion_preset", "byte_idle_hover"),
            beats=tuple(getattr(instruction, "beats", ())),
            fingerprint=fingerprint,
        )

    def _load_definition(self, path: Path) -> CharacterDefinition:
        if not path.is_file():
            raise FileNotFoundError(f"Character definition not found: {path}")
        payload = _parse_character_yaml(path.read_text(encoding="utf-8"))
        return CharacterDefinition.model_validate(payload)

    @staticmethod
    def _validate_required_poses(definition: CharacterDefinition, character_dir: Path) -> None:
        for pose in definition.available_poses:
            _inspect_png((character_dir / definition.asset_directory / f"{pose}.png").resolve())


def _parse_character_yaml(content: str) -> dict[str, object]:
    payload: dict[str, object] = {}
    list_key: str | None = None
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- "):
            if list_key is None:
                raise ValueError("Character YAML list item has no key")
            payload.setdefault(list_key, [])
            value = line[2:].strip()
            items = payload[list_key]
            if not isinstance(items, list):
                raise ValueError(f"Character YAML key {list_key!r} is not a list")
            items.append(value)
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"Character YAML line is not a key/value pair: {raw_line}")
        key = key.strip()
        value = value.strip()
        if value:
            payload[key] = _coerce_scalar(value)
            list_key = None
        else:
            payload[key] = []
            list_key = key
    return payload


def _coerce_scalar(value: str) -> object:
    if value in {"true", "false"}:
        return value == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value.strip('"')


def _inspect_png(path: Path) -> tuple[int, int, bool]:
    if not path.is_file():
        raise FileNotFoundError(f"Character pose asset not found: {path}")
    data = path.read_bytes()
    if len(data) < 33 or not data.startswith(_PNG_SIGNATURE):
        raise ValueError(f"Character pose is not a supported PNG: {path}")
    chunk_type = data[12:16]
    if chunk_type != b"IHDR":
        raise ValueError(f"Character PNG is missing IHDR: {path}")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    bit_depth = data[24]
    color_type = data[25]
    if bit_depth != 8 or color_type not in {4, 6}:
        raise ValueError(f"Character PNG must be 8-bit grayscale-alpha or RGBA: {path}")
    if width < 64 or height < 64 or width > 2048 or height > 2048:
        raise ValueError(f"Character PNG dimensions are outside supported range: {path}")
    return width, height, True


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fingerprint(payload: dict[str, object]) -> str:
    encoded = repr(sorted(payload.items())).encode()
    return hashlib.sha256(encoded).hexdigest()
