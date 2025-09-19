from typing import Dict, List, Optional

from PIL import Image

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
    "radius": {"button": 12, "card": 16, "input": 10, "chip": 12},
    "shadow": {
        "elevation1": "0px 1px 3px rgba(0,0,0,0.18)",
        "elevation2": "0px 6px 20px rgba(0,0,0,0.22)"
    }
}

STEP_DEFINITIONS = [
    {"key": "global_brand_refresh", "label": "Global brand refresh"},
    {"key": "convert_light_mode", "label": "Convert to Light Mode"},
    {"key": "convert_dark_mode", "label": "Convert to Dark Mode"},
    {"key": "primary_actions", "label": "Primary actions"},
    {"key": "secondary_and_links", "label": "Secondary & links"},
    {"key": "surfaces_and_background", "label": "Surfaces & background"},
    {"key": "corner_radii", "label": "Corner radii"},
    {"key": "shadows_and_elevation", "label": "Shadows & elevation"},
    {"key": "hairlines_and_outlines", "label": "Hairlines & outlines"},
    {"key": "charts_and_dataviz", "label": "Charts & dataviz"},
]

STEP_KEY_TO_LABEL = {item["key"]: item["label"] for item in STEP_DEFINITIONS}
STEP_LABEL_TO_KEY = {item["label"]: item["key"] for item in STEP_DEFINITIONS}
ALL_STEP_KEYS: List[str] = [item["key"] for item in STEP_DEFINITIONS]
ALL_STEP_LABELS: List[str] = [item["label"] for item in STEP_DEFINITIONS]
DEFAULT_STEP_KEYS: List[str] = [
    "global_brand_refresh",
    "primary_actions",
    "secondary_and_links",
    "surfaces_and_background",
    "corner_radii",
    "shadows_and_elevation",
    "hairlines_and_outlines",
    "charts_and_dataviz",
]
DEFAULT_STEP_LABELS: List[str] = [STEP_KEY_TO_LABEL[key] for key in DEFAULT_STEP_KEYS]

NEGATIVE_CONSTRAINTS = (
    "Keep the exact UI layout, geometry, spacing, and content unchanged. "
    "Do NOT move, resize, or remove any element. Do not change text content, icons, logos, "
    "photographs, or illustrations. Do not blur. Preserve existing typography and rasterized text. "
    "Only recolor and restyle surfaces, buttons, cards, inputs, switches, outlines, shadows, and other UI chrome "
    "according to the brand tokens. Maintain correct contrast for readability. Do not deviate from the provided hex color values."
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
            "error": "#EF4444",
        },
        "radius": {
            "button": int(radius_button),
            "card": int(radius_card),
            "input": int(radius_input),
            "chip": int(radius_chip),
        },
        "shadow": {
            "elevation1": elevation1,
            "elevation2": elevation2,
        },
    }


def steps_from_labels(labels: List[str]) -> List[str]:
    return [STEP_LABEL_TO_KEY.get(label, label) for label in labels]


def labels_from_keys(keys: List[str]) -> List[str]:
    return [STEP_KEY_TO_LABEL.get(key, key) for key in keys]


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


def _rgb_to_hex(rgb: tuple) -> str:
    r, g, b = rgb[:3]
    return f"#{r:02X}{g:02X}{b:02X}"


def _logo_colors_description(logo: Image.Image, top_n: int = 5) -> str:
    try:
        preview = logo.convert("RGBA").resize((64, 64))
    except Exception:
        return ""
    max_colors = preview.size[0] * preview.size[1]
    colors = preview.getcolors(max_colors)
    if not colors:
        return ""
    dominant: List[str] = []
    for count, color in sorted(colors, key=lambda item: item[0], reverse=True):
        if len(color) == 4 and color[3] < 25:
            continue
        hex_code = _rgb_to_hex(color)
        if hex_code not in dominant:
            dominant.append(hex_code)
        if len(dominant) >= top_n:
            break
    if not dominant:
        return ""
    return ", ".join(dominant)


def _logo_prompt(brand_logo: Optional[Image.Image], brand: str) -> str:
    if brand_logo is None:
        return ""
    colors = _logo_colors_description(brand_logo)
    if colors:
        return (
            f"Logo reference: Preserve the {brand} logo exactly as in the uploaded asset. "
            f"Keep edges crisp, avoid distortion, and ensure logo colors stay true to {colors}."
        )
    return (
        f"Logo reference: Preserve the {brand} logo exactly as in the uploaded asset. "
        "Keep edges crisp and avoid introducing artifacts."
    )


def build_edit_plan(tokens: Dict, steps: List[str], brand_logo: Optional[Image.Image] = None) -> List[Dict]:
    """
    Builds an ordered list of edit steps for Kontext.
    Each step has: name, prompt, negative_prompt, region_hint, strength.
    """
    brand = tokens.get("brand", "Brand")
    colors = _prompt_colors(tokens)
    radii = _prompt_radius(tokens)
    shadows = _prompt_shadow(tokens)
    logo_prompt = _logo_prompt(brand_logo, brand)

    def add_logo(text: str) -> str:
        return text + ("\n\n" + logo_prompt if logo_prompt else "")

    negative = NEGATIVE_CONSTRAINTS
    plan: List[Dict] = []

    requested = set(steps)
    if "convert_light_mode" in requested and "convert_dark_mode" in requested:
        requested.discard("convert_dark_mode")

    if "convert_light_mode" in requested:
        plan.append({
            "name": "Convert to light mode",
            "region_hint": "global",
            "strength": 0.34,
            "prompt": add_logo(
                f"Convert the interface to a LIGHT MODE foundation while preserving layout. "
                f"Use bright neutrals informed by the brand tokens for backgrounds ({tokens['colors']['background']}) using the exact hex values and no tint shifts "
                f"and surfaces ({tokens['colors']['surface']}). Maintain contrast and keep brand accents consistent.\n\n{colors}"
            ),
            "negative_prompt": negative,
        })

    if "convert_dark_mode" in requested:
        plan.append({
            "name": "Convert to dark mode",
            "region_hint": "global",
            "strength": 0.34,
            "prompt": add_logo(
                f"Convert the interface to a DARK MODE foundation while preserving layout. "
                f"Use deep neutrals for backgrounds ({tokens['colors']['background']}) and surfaces ({tokens['colors']['surface']}) while maintaining legibility, matching the exact hex values without hue shifts. "
                f"Keep brand accent colors for interactive elements.\n\n{colors}"
            ),
            "negative_prompt": negative,
        })

    if "global_brand_refresh" in requested:
        plan.append({
            "name": "Global brand refresh",
            "region_hint": "global",
            "strength": 0.36,
            "prompt": add_logo(
                f"Perform a comprehensive {brand} brand refresh on the entire UI screenshot while preserving layout and textual content. "
                f"Replace any legacy accent colors with the supplied palette: primary {tokens['colors']['primary']}, secondary {tokens['colors']['secondary']}, link {tokens['colors']['link']}, success {tokens['colors']['success']}, warning {tokens['colors']['warning']}, error {tokens['colors']['error']}. "
                f"Apply the background {tokens['colors']['background']} and surface {tokens['colors']['surface']} hex values across cards, panels, and chrome, ensuring they are visibly updated. "
                f"Ensure buttons, inputs, chips, and tabs reflect the brand's hierarchy, radii, and shadows so the output unmistakably matches {brand}. "
                f"Make the transformation clearly different from the original while keeping geometry and content untouched.\n\n{colors}{radii}{shadows}"
            ),
            "negative_prompt": negative,
        })

    ordered_followups = [
        "primary_actions",
        "secondary_and_links",
        "surfaces_and_background",
        "corner_radii",
        "shadows_and_elevation",
        "hairlines_and_outlines",
        "charts_and_dataviz",
    ]

    for key in ordered_followups:
        if key not in requested:
            continue
        if key == "primary_actions":
            plan.append({
                "name": "Primary actions",
                "region_hint": "global",
                "strength": 0.33,
                "prompt": add_logo(
                    f"Apply the {brand} design system to PRIMARY actions and interactive elements. "
                    f"Recolor primary buttons, toggles, active tabs, sliders, and key accent chips to the brand primary color using the exact hex value {tokens['colors']['primary']} with no gradients or hue shifts. "
                    f"Replace any previous accent colors so all primary UI controls match {tokens['colors']['primary']}. Do not move or resize elements. Ensure text remains legible on primary surfaces.\n\n{colors}"
                ),
                "negative_prompt": negative,
            })
        elif key == "secondary_and_links":
            plan.append({
                "name": "Secondary & Links",
                "region_hint": "global",
                "strength": 0.31,
                "prompt": add_logo(
                    f"Style SECONDARY actions and LINKS. Use the exact hex values {tokens['colors']['secondary']} and {tokens['colors']['link']} for secondary accents and links while keeping iconography and text unchanged. "
                    f"Replace any residual legacy colors on secondary buttons, ghost buttons, inline links, and hover states with the brand palette. Do not alter layout; adjust only color accents and subtle hover/active states consistent with the brand.\n\n{colors}"
                ),
                "negative_prompt": negative,
            })
        elif key == "surfaces_and_background":
            plan.append({
                "name": "Surfaces & Background",
                "region_hint": "global",
                "strength": 0.31,
                "prompt": add_logo(
                    f"Normalize BACKGROUNDS and SURFACES to the brand tokens. Set the page background and app surfaces to the exact hex values {tokens['colors']['background']} and {tokens['colors']['surface']} with no color drift. "
                    f"Ensure contrast with existing text. Do not modify photographs or illustrations.\n\n{colors}"
                ),
                "negative_prompt": negative,
            })
        elif key == "corner_radii":
            plan.append({
                "name": "Corner radii",
                "region_hint": "global",
                "strength": 0.29,
                "prompt": add_logo(
                    f"Adjust corner radii of UI rectangles to match the brand tokens without moving elements. Buttons → {tokens['radius']['button']}px; "
                    f"Cards → {tokens['radius']['card']}px; Inputs → {tokens['radius']['input']}px; Chips → {tokens['radius']['chip']}px. "
                    f"Ensure every relevant component reflects these radii so the change is visible. Preserve layout and spacing exactly.\n\n{radii}"
                ),
                "negative_prompt": negative,
            })
        elif key == "shadows_and_elevation":
            plan.append({
                "name": "Shadows & Elevation",
                "region_hint": "global",
                "strength": 0.27,
                "prompt": add_logo(
                    f"Apply subtle brand-consistent shadows to cards, modals, and popovers. Use elevation1 for small components and elevation2 for raised surfaces. "
                    f"Keep edges crisp and avoid haloing. Do not blur the entire image.\n\n{shadows}"
                ),
                "negative_prompt": negative,
            })
        elif key == "hairlines_and_outlines":
            plan.append({
                "name": "Hairlines & Outlines",
                "region_hint": "global",
                "strength": 0.25,
                "prompt": add_logo(
                    "Unify hairlines, dividers, and input outlines to neutral tints that match the brand surfaces while keeping contrast. "
                    "Do not thicken lines; preserve geometry and spacing."
                ),
                "negative_prompt": negative,
            })
        elif key == "charts_and_dataviz":
            plan.append({
                "name": "Charts & Dataviz",
                "region_hint": "global",
                "strength": 0.29,
                "prompt": add_logo(
                    f"Recolor chart lines, bars, and category swatches to the brand palette (primary, secondary, success, warning, error) while preserving data positions and exact chart geometry. "
                    f"Do not change labels or scales.\n\n{colors}"
                ),
                "negative_prompt": negative,
            })

    return plan
