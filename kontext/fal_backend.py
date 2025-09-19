"""
FAL backend for FLUX.1 Kontext [dev] editing.
Requires:
  pip install fal-client requests pillow
Env:
  export FAL_KEY=YOUR_FAL_API_KEY   # or FAL_API_KEY (mapped automatically)
"""
import io
import os
from typing import Any, Dict, Optional

import requests
from PIL import Image

_STATE = {"ready": False}


def init() -> None:
    """Verify SDK + API key (idempotent)."""
    if _STATE["ready"]:
        return
    try:
        import fal_client  # noqa: F401
    except Exception as e:
        raise RuntimeError("fal-client not installed. Run: pip install fal-client") from e

    if os.getenv("FAL_KEY") is None and os.getenv("FAL_API_KEY"):
        os.environ["FAL_KEY"] = os.getenv("FAL_API_KEY")
    if os.getenv("FAL_KEY") is None:
        raise RuntimeError("Missing FAL API key. Set FAL_KEY or FAL_API_KEY.")

    _STATE["ready"] = True


def _image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


def _upload_image_to_fal(img: Image.Image) -> str:
    """Upload input image → get URL for image_url."""
    import fal_client
    try:
        return fal_client.upload_image(img, format="png")
    except Exception:
        data = _image_to_bytes(img, "PNG")
        try:
            return fal_client.upload(data, content_type="image/png", file_name="input.png")
        except Exception as e:
            raise RuntimeError("FAL upload failed. Try: pip install -U fal-client") from e


def _first_image_url(result: Dict[str, Any]) -> Optional[str]:
    """Extract image URL from various FAL response shapes."""
    if not isinstance(result, dict):
        return None
    for key in ("images", "image", "output", "outputs", "content", "data"):
        if key in result:
            obj = result[key]
            if isinstance(obj, dict):
                for k in ("url", "image_url", "href"):
                    if isinstance(obj.get(k), str):
                        return obj[k]
            if isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        for k in ("url", "image_url", "href"):
                            if isinstance(item.get(k), str):
                                return item[k]
    for k in ("url", "image_url", "href"):
        v = result.get(k)
        if isinstance(v, str):
            return v
    return None


def _download(url: str) -> Image.Image:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content)).convert("RGBA")


def apply_edit(
    image: Image.Image,
    prompt: str,
    negative_prompt: str = "",
    strength: float = 0.3,  # kept for API compat
    seed: int = 0,          # forwarded to API when available
    region_hint: str = "global",
) -> Image.Image:
    """
    Call: fal-ai/flux-kontext/dev via fal_client.subscribe, then return edited PIL image.
    We append the negative prompt as 'Constraints:' to match the available arguments.
    """
    init()
    import fal_client

    combined_prompt = prompt.strip()
    if negative_prompt:
        combined_prompt += "\n\nConstraints: " + negative_prompt.strip()

    image_url = _upload_image_to_fal(image)

    args: Dict[str, Any] = {
        "prompt": combined_prompt,
        "image_url": image_url,
        "num_inference_steps": 28,
        "guidance_scale": 2.5,
        "num_images": 1,
        "enable_safety_checker": True,
        "output_format": "png",
        "acceleration": "none",
        "resolution_mode": "match_input",
    }
    if isinstance(seed, int) and seed > 0:
        args["seed"] = seed

    def _on_queue_update(update):
        try:
            if isinstance(update, fal_client.InProgress):
                for log in getattr(update, "logs", []) or []:
                    msg = log.get("message")
                    if msg:
                        print(msg)
        except Exception:
            pass

    result = fal_client.subscribe(
        "fal-ai/flux-kontext/dev",
        arguments=args,
        with_logs=True,
        on_queue_update=_on_queue_update,
    )

    out_url = _first_image_url(result)
    if not out_url:
        # Fallback if SDK returns base64 fields (rare)
        if isinstance(result, dict):
            b64 = result.get("image_base64") or result.get("output_base64")
            if b64:
                import base64
                data = base64.b64decode(b64)
                return Image.open(io.BytesIO(data)).convert("RGBA")
        raise RuntimeError(f"FAL response had no output URL: {result}")

    return _download(out_url)
