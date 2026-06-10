"""Image generator — mock provider for v1; real providers pluggable later."""

from __future__ import annotations

import uuid
from pathlib import Path

from workers.config import DEFAULT_IMAGE_PROVIDER, IMAGES_OUT_DIR
from workers.models import ImageAsset, ScenePlan


def generate_images(
    scene_plan: ScenePlan,
    provider: str | None = None,
    output_dir: Path | None = None,
) -> list[ImageAsset]:
    """Generate image assets for each scene. Returns mock metadata in v1."""
    provider = provider or DEFAULT_IMAGE_PROVIDER
    output_dir = output_dir or IMAGES_OUT_DIR

    if provider != "mock":
        import warnings
        warnings.warn(
            f"Image provider '{provider}' not implemented in v1. Using mock.",
            stacklevel=2,
        )

    assets: list[ImageAsset] = []
    for scene in scene_plan.scenes:
        asset_id = f"img_{uuid.uuid4().hex[:8]}"
        image_path = str(output_dir / f"{asset_id}.png") if provider != "mock" else None
        asset = ImageAsset(
            id=asset_id,
            scene_number=scene.scene_number,
            scene_plan_id=scene_plan.id,
            provider=provider,
            image_path=image_path,
            image_prompt=scene.image_prompt,
        )
        assets.append(asset)
    return assets
