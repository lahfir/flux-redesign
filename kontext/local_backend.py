"""
Local backend stub for Kontext [dev]. Returns input unchanged.
You can wire Diffusers/ComfyUI here later if you want an offline path.
"""
from PIL import Image


def init() -> None:
    pass


def apply_edit(
    image: Image.Image,
    prompt: str,
    negative_prompt: str = "",
    strength: float = 0.3,
    seed: int = 0,
    region_hint: str = "global",
) -> Image.Image:
    return image
