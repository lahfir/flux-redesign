import io
import json
import secrets
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

from kontext import fal_backend, local_backend


def _apply_edit(
    backend: str,
    image: Image.Image,
    prompt: str,
    negative_prompt: str,
    strength: float,
    seed: int,
    region_hint: str,
) -> Image.Image:
    if backend == "FAL (Kontext API)":
        fal_backend.init()
        return fal_backend.apply_edit(
            image=image,
            prompt=prompt,
            negative_prompt=negative_prompt,
            strength=strength,  # kept for API compat
            seed=seed,
            region_hint=region_hint,
        )
    elif backend == "local (Kontext)":
        local_backend.init()
        return local_backend.apply_edit(
            image=image,
            prompt=prompt,
            negative_prompt=negative_prompt,
            strength=strength,
            seed=seed,
            region_hint=region_hint,
        )
    else:
        # dry-run: return input unchanged
        return image


def _resolve_seed(base_seed: int, step_index: int, jitter: bool) -> int:
    if base_seed is None or base_seed <= 0:
        return secrets.randbelow(1_000_000_000)
    if jitter:
        return (base_seed + step_index) % 1_000_000_000
    return base_seed


def run_restyle_plan(
    image: Image.Image,
    plan: List[Dict],
    seed: int,
    backend: str,
    strength_multiplier: float,
    seed_jitter: bool,
    save_dir: Path,
    brand_logo: Optional[Image.Image] = None,
) -> Tuple[List[Image.Image], List[str]]:
    """
    Iterate through plan steps, call backend, collect outputs.
    """
    out_frames: List[Image.Image] = []
    logs: List[str] = []
    current = image.copy()
    save_dir.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex[:8]
    run_path = save_dir / f"restyle_{run_id}"
    run_path.mkdir(parents=True, exist_ok=True)

    if brand_logo is not None:
        try:
            logo_path = save_image(brand_logo.convert("RGBA"), run_path, "brand_logo.png")
            logs.append(f"[logo] Saved brand logo reference to: {logo_path}")
        except Exception as exc:
            logs.append(f"[logo] Failed to save brand logo reference: {exc}")

    for idx, step in enumerate(plan):
        step_seed = _resolve_seed(seed, idx, seed_jitter)
        s = max(0.05, float(step.get("strength", 0.3)) * float(strength_multiplier))
        prompt = step["prompt"]
        negative = step["negative_prompt"]
        region = step.get("region_hint", "global")
        name = step.get("name", f"step_{idx+1}")

        # Save prompt as reference
        (run_path / f"{idx:02d}_{name}_prompt.txt").write_text(
            f"PROMPT:\n{prompt}\n\nNEGATIVE:\n{negative}\n", encoding="utf-8"
        )

        out = _apply_edit(
            backend=backend,
            image=current,
            prompt=prompt,
            negative_prompt=negative,
            strength=s,
            seed=step_seed,
            region_hint=region,
        )
        out_frames.append(out)
        out_path = save_image(out, run_path, f"{idx:02d}_{name}.png")
        logs.append(
            f"[{idx+1}/{len(plan)}] {name} (seed={step_seed}, strength={s:.2f}) → {out_path}"
        )
        current = out

    return out_frames, logs


def save_image(img: Image.Image, folder: Path, filename: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    img.save(path)
    return path
