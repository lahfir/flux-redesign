from typing import Dict, List

EXAMPLE_TOKENS: Dict = {
    "brand": "Algominds",
    "colors": {
        "primary": "#C6FF00",
        "secondary": "#00E5FF",
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

DEFAULT_STEPS_ORDER = [
    "primary_actions",
    "secondary_and_links",
    "surfaces_and_background",
    "corner_radii",
    "shadows_and_elevation",
    "hairlines_and_outlines",
    "charts_and_dataviz"
]

NEGATIVE_CONSTRAINTS = (
    "Keep the exact UI layout, geometry, spacing, and content unchanged. "
    "Do NOT move, resize, or remove any element. Do not change text content, icons, logos, "
    "photographs, or illustrations. Do not blur. Preserve existing typography and rasterized text. "
    "Only recolor and restyle surfaces, buttons, cards, inputs, switches, outlines, shadows, and other UI chrome "
    "according to the brand tokens. Maintain correct contrast for readability."
)


def load_tokens_from_json(text: str) -> Dict:
    import json
    tokens = json.loads(text)
    assert "colors" in tokens and "radius" in tokens and "shadow" in tokens, "Missing keys in tokens JSON."
    return tokens


def tokens_from_simple_form(
    brand: str,
    primary: str,
    secondary: str,
    background: str,
    surface: str,
    link: str,
    text_on_dark: str,
    text_on_light: str,
    radius_button: int,
    radius_card: int,
    radius_input: int,
    radius_chip: int,
    elevation1: str,
    elevation2: str,
) -> Dict:
    return {
        "brand": brand,
        "colors": {
            "primary": primary,
            "secondary": secondary,
            "background": background,
            "surface": surface,
            "text_on_dark": text_on_dark,
            "text_on_light": text_on_light,
            "link": link,
            "success": "#22C55E",
            "warning": "#F59E0B",
            "error": "#EF4444"
        },
        "radius": {
            "button": int(radius_button),
            "card": int(radius_card),
            "input": int(radius_input),
            "chip": int(radius_chip)
        },
        "shadow": {
            "elevation1": elevation1,
            "elevation2": elevation2
        }
    }


def _prompt_colors(tokens: Dict) -> str:
    c = tokens["colors"]
    return (
        f"Brand colors:\n"
        f"- primary: {c['primary']}\n"
        f"- secondary: {c['secondary']}\n"
        f"- link: {c['link']}\n"
        f"- background: {c['background']}\n"
        f"- surface: {c['surface']}\n"
        f"- text on dark: {c['text_on_dark']}\n"
        f"- text on light: {c['text_on_light']}\n"
        f"- semantic: success {c['success']}, warning {c['warning']}, error {c['error']}\n"
    )


def _prompt_radius(tokens: Dict) -> str:
    r = tokens["radius"]
    return (
        f"Corner radii to apply:\n"
        f"- buttons: {r['button']}px\n"
        f"- cards: {r['card']}px\n"
        f"- inputs: {r['input']}px\n"
        f"- chips: {r['chip']}px\n"
    )


def _prompt_shadow(tokens: Dict) -> str:
    s = tokens["shadow"]
    return (
        f"Shadow styles:\n"
        f"- elevation1: {s['elevation1']}\n"
        f"- elevation2: {s['elevation2']}\n"
    )


def build_edit_plan(tokens: Dict, steps: List[str]) -> List[Dict]:
    """
    Builds an ordered list of edit steps for Kontext.
    Each step has: name, prompt, negative_prompt, region_hint, strength.
    """
    brand = tokens.get("brand", "Brand")
    colors = _prompt_colors(tokens)
    radii = _prompt_radius(tokens)
    shadows = _prompt_shadow(tokens)

    # Base “freeze layout” clause:
    negative = NEGATIVE_CONSTRAINTS

    plan: List[Dict] = []

    if "primary_actions" in steps:
        plan.append({
            "name": "Primary actions",
            "region_hint": "global",
            "strength": 0.32,
            "prompt": (
                f"Apply the {brand} design system to PRIMARY actions and interactive elements. "
                f"Recolor primary buttons, toggles, active tabs, sliders, and key accent chips to the brand primary color. "
                f"Do not move or resize elements. Ensure text remains legible on primary surfaces.\n\n{colors}"
            ),
            "negative_prompt": negative
        })

    if "secondary_and_links" in steps:
        plan.append({
            "name": "Secondary & Links",
            "region_hint": "global",
            "strength": 0.30,
            "prompt": (
                f"Style SECONDARY actions and LINKS. "
                f"Use the brand secondary and link colors. "
                f"Keep iconography and text unchanged. "
                f"Do not alter layout; adjust only color accents and subtle hover/active states consistent with the brand.\n\n{colors}"
            ),
            "negative_prompt": negative
        })

    if "surfaces_and_background" in steps:
        plan.append({
            "name": "Surfaces & Background",
            "region_hint": "global",
            "strength": 0.30,
            "prompt": (
                f"Normalize BACKGROUNDS and SURFACES to the brand tokens. "
                f"Set the page background and app surfaces to {tokens['colors']['background']} and {tokens['colors']['surface']}. "
                f"Ensure contrast with existing text. "
                f"Do not modify photographs or illustrations.\n\n{colors}"
            ),
            "negative_prompt": negative
        })

    if "corner_radii" in steps:
        plan.append({
            "name": "Corner radii",
            "region_hint": "global",
            "strength": 0.28,
            "prompt": (
                f"Adjust corner radii of UI rectangles to match the brand tokens without moving elements. "
                f"Buttons → {tokens['radius']['button']}px; Cards → {tokens['radius']['card']}px; "
                f"Inputs → {tokens['radius']['input']}px; Chips → {tokens['radius']['chip']}px. "
                f"Preserve layout and spacing exactly.\n\n{radii}"
            ),
            "negative_prompt": negative
        })

    if "shadows_and_elevation" in steps:
        plan.append({
            "name": "Shadows & Elevation",
            "region_hint": "global",
            "strength": 0.26,
            "prompt": (
                f"Apply subtle brand-consistent shadows to cards, modals, and popovers. "
                f"Use elevation1 for small components and elevation2 for raised surfaces. "
                f"Keep edges crisp and avoid haloing. Do not blur the entire image.\n\n{shadows}"
            ),
            "negative_prompt": negative
        })

    if "hairlines_and_outlines" in steps:
        plan.append({
            "name": "Hairlines & Outlines",
            "region_hint": "global",
            "strength": 0.24,
            "prompt": (
                f"Unify hairlines, dividers, and input outlines to neutral tints that match the brand surfaces while keeping contrast. "
                f"Do not thicken lines; preserve geometry and spacing."
            ),
            "negative_prompt": negative
        })

    if "charts_and_dataviz" in steps:
        plan.append({
            "name": "Charts & Dataviz",
            "region_hint": "global",
            "strength": 0.28,
            "prompt": (
                f"Recolor chart lines, bars, and category swatches to brand palette "
                f"(primary, secondary, success, warning, error) while preserving data positions and exact chart geometry. "
                f"Do not change labels or scales.\n\n{colors}"
            ),
            "negative_prompt": negative
        })

    return plan
