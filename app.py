import io
import json
import os
from pathlib import Path
from typing import List, Optional, Tuple

import gradio as gr
from PIL import Image

# Local imports
from kontext.runner import run_restyle_plan, save_image
from restyle.planner import (
    EXAMPLE_TOKENS,
    load_tokens_from_json,
    tokens_from_simple_form,
    build_edit_plan,
    DEFAULT_STEP_KEYS,
    DEFAULT_STEP_LABELS,
    ALL_STEP_LABELS,
    steps_from_labels,
)

# Load .env if present
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

ROOT = Path(__file__).parent.resolve()
TOKENS_PATH = ROOT / "scripts" / "tokens" / "example_tokens.json"


def _load_sample_tokens() -> str:
    if TOKENS_PATH.exists():
        return TOKENS_PATH.read_text(encoding="utf-8")
    return json.dumps(EXAMPLE_TOKENS, indent=2)


def on_click_build_tokens(
    brand_name,
    primary,
    secondary,
    background,
    surface,
    link,
    text_on_dark,
    text_on_light,
    radius_button,
    radius_card,
    radius_input,
    radius_chip,
    shadow_e1,
    shadow_e2,
):
    tokens = tokens_from_simple_form(
        brand=brand_name or "YourBrand",
        primary=primary or "#4F46E5",
        secondary=secondary or "#06B6D4",
        background=background or "#0B0B0B",
        surface=surface or "#121212",
        link=link or "#6EA8FE",
        text_on_dark=text_on_dark or "#FFFFFF",
        text_on_light=text_on_light or "#111111",
        radius_button=int(radius_button or 12),
        radius_card=int(radius_card or 16),
        radius_input=int(radius_input or 10),
        radius_chip=int(radius_chip or 12),
        elevation1=shadow_e1 or "0px 1px 3px rgba(0,0,0,0.18)",
        elevation2=shadow_e2 or "0px 6px 20px rgba(0,0,0,0.22)",
    )
    return json.dumps(tokens, indent=2)


def on_click_restyle(
    image: Image.Image,
    brand_logo: Optional[Image.Image],
    tokens_json: str,
    steps_labels: List[str],
    seed: int,
    strength_mult: float,
    backend: str,
    jitter: bool,
    show_step_outputs: bool,
) -> Tuple[Image.Image, List[Image.Image], str]:
    if image is None:
        raise gr.Error("Please upload a screenshot image (PNG/JPG).")

    try:
        tokens = load_tokens_from_json(tokens_json)
    except Exception as e:
        raise gr.Error(f"Invalid tokens JSON: {e}")

    step_keys = steps_from_labels(steps_labels)
    if not step_keys:
        step_keys = list(DEFAULT_STEP_KEYS)

    if "convert_light_mode" in step_keys and "convert_dark_mode" in step_keys:
        raise gr.Error("Select either light mode or dark mode conversion, not both.")

    # Build edit plan (ordered steps with prompts)
    plan = build_edit_plan(tokens=tokens, steps=step_keys, brand_logo=brand_logo)

    # Run plan via Kontext backend
    outputs, log = run_restyle_plan(
        image=image.convert("RGBA"),
        plan=plan,
        seed=seed,
        backend=backend,
        strength_multiplier=strength_mult,
        seed_jitter=jitter,
        save_dir=ROOT / "outputs",
        brand_logo=brand_logo,
    )

    final_img = outputs[-1] if outputs else image
    # Save final image for convenience
    out_path = save_image(final_img, ROOT / "outputs", "final.png")

    info = f"Saved final image to: {out_path}\n\n" + "\n".join(log)
    gallery = outputs if show_step_outputs else []
    return final_img, gallery, info


with gr.Blocks(title="Design-System Restyler — FLUX.1 Kontext [dev]") as demo:
    gr.Markdown(
        """
# Design-System Restyler — Instant brand theme on UI screenshots
**Powered by FLUX.1 Kontext [dev] via FAL**.  
Drop a UI screenshot and apply your brand tokens (colors, corner radii, shadows) while **freezing layout & content**.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            image = gr.Image(type="pil", label="Upload app screenshot")
            brand_logo = gr.Image(type="pil", label="Upload brand logo (optional)", height=200)
            gr.Markdown("### Brand Tokens — Quick Form")
            brand_name = gr.Textbox(label="Brand name", value="Algominds")
            with gr.Row():
                primary = gr.ColorPicker(label="Primary", value="#C6FF00")
                secondary = gr.ColorPicker(label="Secondary", value="#00E5FF")
                link = gr.ColorPicker(label="Link", value="#6EA8FE")
            with gr.Row():
                background = gr.ColorPicker(label="Background", value="#0B0B0B")
                surface = gr.ColorPicker(label="Surface", value="#121212")
            with gr.Row():
                text_on_dark = gr.ColorPicker(label="Text on dark", value="#FFFFFF")
                text_on_light = gr.ColorPicker(label="Text on light", value="#111111")
            with gr.Row():
                radius_button = gr.Number(label="Radius: Button", value=12)
                radius_card = gr.Number(label="Radius: Card", value=16)
                radius_input = gr.Number(label="Radius: Input", value=10)
                radius_chip = gr.Number(label="Radius: Chip", value=12)
            with gr.Row():
                shadow_e1 = gr.Textbox(label="Shadow: Elevation1", value="0px 1px 3px rgba(0,0,0,0.18)")
                shadow_e2 = gr.Textbox(label="Shadow: Elevation2", value="0px 6px 20px rgba(0,0,0,0.22)")
            build_btn = gr.Button("Build tokens JSON from form")

        with gr.Column(scale=1):
            gr.Markdown("### Brand Tokens JSON")
            tokens_json = gr.Code(
                label="Tokens JSON",
                language="json",
                value=_load_sample_tokens(),
                lines=26,
            )
            load_sample = gr.Button("Load sample tokens")
            with gr.Accordion("Steps to run", open=True):
                steps = gr.CheckboxGroup(
                    choices=ALL_STEP_LABELS,
                    value=DEFAULT_STEP_LABELS,
                    label="Select steps",
                )
            with gr.Row():
                backend = gr.Radio(
                    choices=["FAL (Kontext API)", "local (Kontext)", "dry-run (no model)"],
                    value="FAL (Kontext API)",
                    label="Backend",
                )
                seed = gr.Slider(0, 999999, value=12345, step=1, label="Seed")
            with gr.Row():
                strength_mult = gr.Slider(0.1, 1.5, value=1.0, step=0.05, label="Global strength multiplier")
                jitter = gr.Checkbox(value=True, label="Seed jitter (+idx)")
                show_gallery = gr.Checkbox(value=True, label="Show step outputs")
            restyle_btn = gr.Button("Restyle Screenshot", variant="primary")

        with gr.Column(scale=1):
            result = gr.Image(type="pil", label="Final Restyled Image")
            gallery = gr.Gallery(label="Step Outputs", columns=3, height=300)
            info = gr.Textbox(label="Logs & saved paths", lines=16)

    # Wiring
    build_btn.click(
        on_click_build_tokens,
        inputs=[
            brand_name,
            primary,
            secondary,
            background,
            surface,
            link,
            text_on_dark,
            text_on_light,
            radius_button,
            radius_card,
            radius_input,
            radius_chip,
            shadow_e1,
            shadow_e2,
        ],
        outputs=[tokens_json],
    )
    load_sample.click(lambda: _load_sample_tokens(), outputs=[tokens_json])

    restyle_btn.click(
        on_click_restyle,
        inputs=[
            image,
            brand_logo,
            tokens_json,
            steps,
            seed,
            strength_mult,
            backend,
            jitter,
            show_gallery,
        ],
        outputs=[result, gallery, info],
    )

if __name__ == "__main__":
    demo.launch()
