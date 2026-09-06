from pathlib import Path

import pytest

from short_video_generator.contracts import PresenterInstruction
from short_video_generator.providers.characters import LocalCharacterAssetProvider


def test_local_character_provider_resolves_pose_with_stable_fingerprint() -> None:
    provider = LocalCharacterAssetProvider(Path("assets/characters"))
    instruction = PresenterInstruction(
        character_id="byte",
        pose="explaining",
        position="bottom_right",
        scale=0.32,
    )

    first = provider.resolve(instruction, scene_order=1)
    second = provider.resolve(instruction, scene_order=1)

    assert first.character_id == "byte"
    assert first.pose == "explaining"
    assert first.asset_relative_path == Path("assets/characters/byte/explaining.png")
    assert first.has_alpha is True
    assert first.width >= 64
    assert first.height >= 64
    assert first.fingerprint == second.fingerprint


def test_local_character_provider_fails_for_missing_character() -> None:
    provider = LocalCharacterAssetProvider(Path("assets/characters"))

    with pytest.raises(FileNotFoundError, match="Character definition not found"):
        provider.resolve(
            PresenterInstruction(character_id="missing", pose="neutral"),
            scene_order=1,
        )


def test_local_character_provider_falls_back_for_missing_pose() -> None:
    provider = LocalCharacterAssetProvider(Path("assets/characters"))

    reference = provider.resolve(
        PresenterInstruction(character_id="byte", pose="moonwalk"),
        scene_order=1,
    )

    assert reference.pose == "neutral"
    assert reference.requested_pose == "moonwalk"
    assert reference.fallback_reason is not None
