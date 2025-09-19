# Design-System Restyler — FLUX.1 Kontext [dev]
Restyle an **app screenshot** to your **brand tokens** (colors, corner radii, shadows) while **freezing layout**.  
Built on **FLUX.1 Kontext [dev]** (open-weights editing model) via **FAL**.

## How it works
We build an ordered **edit plan** from your tokens (primary, secondary, surfaces, radii, shadows) and run **iterative Kontext edits**.  
Each step uses a precise prompt plus strong **constraints** (negative prompt) to preserve layout & content.

## FAL usage (embedded reference)
We follow the official usage pattern for Kontext [dev] on FAL:

```python
import fal_client

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(log["message"])

result = fal_client.subscribe(
    "fal-ai/flux-kontext/dev",
    arguments={
        "prompt": "Change the setting to a day time, add a lot of people walking the sidewalk while maintaining the same style of the painting",
        "image_url": "https://storage.googleapis.com/falserverless/example_inputs/kontext_example_input.webp",
        "num_inference_steps": 28,
        "guidance_scale": 2.5,
        "num_images": 1,
        "enable_safety_checker": True,
        "output_format": "jpeg",
        "acceleration": "none",
        "resolution_mode": "match_input"
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)
```

**In this repo**, we upload your local image to FAL, call:

```
fal_client.subscribe("fal-ai/flux-kontext/dev", arguments={
  "prompt": "<your edit prompt>\n\nConstraints: <negative prompt>",
  "image_url": "<uploaded-url>",
  "num_inference_steps": 28,
  "guidance_scale": 2.5,
  "num_images": 1,
  "enable_safety_checker": true,
  "output_format": "png",
  "acceleration": "none",
  "resolution_mode": "match_input"
})
```

Then we download the first output image URL and continue to the next step.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && $EDITOR .env    # set FAL_KEY
python app.py
```

## Using the app

1. Upload a **UI screenshot** (PNG/JPG).
2. Edit tokens via the form or the JSON (see `scripts/tokens/example_tokens.json`).
3. Pick which **steps** to run and hit **Restyle**.
4. The app shows step outputs and saves everything under `outputs/`.

### Token schema

```json
{
  "brand": "Acme",
  "colors": {
    "primary": "#4F46E5",
    "secondary": "#06B6D4",
    "background": "#0B0B0B",
    "surface": "#121212",
    "text_on_dark": "#FFFFFF",
    "text_on_light": "#111111",
    "link": "#6EA8FE",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "error": "#EF4444"
  },
  "radius": { "button": 12, "card": 16, "input": 10, "chip": 12 },
  "shadow": {
    "elevation1": "0px 1px 3px rgba(0,0,0,0.18)",
    "elevation2": "0px 6px 20px rgba(0,0,0,0.22)"
  }
}
```

## Prompts (example)

* **Primary actions:** “Apply the design system to primary actions: recolor buttons/toggles/active tabs to {primary}. Ensure legible text.”
* **Secondary & links:** “Use {secondary} and {link} without altering layout.”
* **Surfaces:** “Normalize backgrounds to {background}/{surface}; don’t touch photos/illustrations.”
* **Radii:** “Adjust corners: buttons {b}px, cards {c}px, inputs {i}px, chips {ch}px.”
* **Shadows:** “Apply subtle {elevation1}/{elevation2} on cards/modals; avoid global blur.”
* **Constraints (always appended):** Keep geometry/spacing/content unchanged; no text/icon changes.

## Notes

* Default backend is **FAL** (Kontext [dev]); set `FAL_KEY` or `FAL_API_KEY`.
* Local backend is a stub (returns image unchanged) to keep the code modular if you want offline later.
* Respect model licensing for your use case.

## Demo script (≤3 min)

1. Hook: show original vs restyled split-view.
2. Tokens → plan → one step run (primary) → next (surfaces) → final.
3. Second brand style swap in 15 seconds.
4. Close: “Layout frozen; only visual theme updated — built with Kontext [dev] on FAL.”

---

**Hackathon deadline:** Sep 25, 2025 @ 5:45pm EDT (Devpost).
