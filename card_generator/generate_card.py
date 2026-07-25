#!/usr/bin/env python3
"""
============================================================
 Card Generator  --  Design-forward shareable card creator
============================================================

Generates a visually polished share card with QR code.
Inputs: website URL, model name, reference UI screenshot.
Output: a designer-grade .png card ready for distribution.

Design philosophy (inspired by canvas-design):
  Each card is treated as a curated visual artifact, not a
  utilitarian layout. Composition, color, typography, and
  spatial balance are given the same weight as information
  delivery. The result should feel meticulously crafted —
  the product of deep expertise and painstaking attention.

Usage:
    python generate_card.py --url https://example.com --name "My Model" --image ui.png
    python generate_card.py --url https://example.com --name "My Model" --image ui.png --theme tech
"""

import argparse
import os
import sys

import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ================================================================
#  DESIGN THEMES (inspired by canvas-design visual philosophies)
#  Each theme defines a palette, a mood, and layout proportions.
# ================================================================

THEMES = {
    "minimal": {
        "name": "Geometric Silence",
        "description": "Pure order and restraint. Swiss formalism with generous negative space.",
        "bg": (250, 249, 245),          # warm off-white
        "text_primary": (20, 20, 19),   # near-black
        "text_secondary": (145, 140, 130),
        "accent": (140, 156, 118),      # muted green
        "accent_alt": (176, 174, 165),   # mid gray
        "divider": (232, 230, 220),
        "card_padding": 48,
        "ui_border_radius": 12,
        "qr_padding": 16,
        "font_ratio": {"heading": 1.0, "body": 0.55, "caption": 0.36},
    },
    "tech": {
        "name": "Chromatic Systems",
        "description": "Digital precision meets data-visualization aesthetics.",
        "bg": (13, 17, 23),             # deep dark
        "text_primary": (230, 237, 243),
        "text_secondary": (139, 148, 158),
        "accent": (88, 166, 255),       # electric blue
        "accent_alt": (63, 185, 80),     # signal green
        "divider": (48, 54, 61),
        "card_padding": 40,
        "ui_border_radius": 8,
        "qr_padding": 12,
        "font_ratio": {"heading": 1.0, "body": 0.53, "caption": 0.35},
    },
    "organic": {
        "name": "Natural Clustering",
        "description": "Warm, rounded forms with color drawn from earth and architecture.",
        "bg": (248, 244, 235),          # cream
        "text_primary": (58, 46, 35),
        "text_secondary": (141, 121, 98),
        "accent": (217, 119, 87),       # terracotta
        "accent_alt": (120, 140, 93),    # olive
        "divider": (225, 216, 200),
        "card_padding": 44,
        "ui_border_radius": 16,
        "qr_padding": 14,
        "font_ratio": {"heading": 1.0, "body": 0.56, "caption": 0.37},
    },
    "bold": {
        "name": "Concrete Poetry",
        "description": "Monumental form and bold geometry. Polish poster energy.",
        "bg": (20, 20, 19),             # deep black
        "text_primary": (250, 249, 245),
        "text_secondary": (176, 174, 165),
        "accent": (217, 119, 87),       # burnt orange
        "accent_alt": (106, 155, 204),   # slate blue
        "divider": (58, 56, 52),
        "card_padding": 36,
        "ui_border_radius": 4,
        "qr_padding": 10,
        "font_ratio": {"heading": 1.0, "body": 0.52, "caption": 0.34},
    },
}

# ================================================================
#  CARD CONFIGURATION
# ================================================================

CARD_WIDTH = 1000
CARD_HEIGHT = 620

UI_MAX_WIDTH = 420
UI_MAX_HEIGHT = 300
QR_SIZE = 180

# ================================================================
#  FONT HELPERS
# ================================================================

_FONT_CACHE = {}


def _resolve_font(size, prefer_bold=False):
    """Resolve the best available font at *size* px."""
    key = (size, prefer_bold)
    if key in _font_cache:
        return _font_cache[key]

    candidates = []
    if prefer_bold:
        candidates = [
            "segoeuib.ttf", "seguisb.ttf",
            "msyhbd.ttf", "simhei.ttf",
            "arialbd.ttf", "arial.ttf",
        ]
    else:
        candidates = [
            "segoeui.ttf", "segoe.ttf",
            "msyh.ttc", "msyh.ttf",
            "simhei.ttf", "arial.ttf",
        ]

    for name in candidates:
        for root in [os.environ.get("WINDIR", r"C:\Windows") + r"\Fonts", ""]:
            path = os.path.join(root, name) if root else name
            try:
                font = ImageFont.truetype(path, size)
                _font_cache[key] = font
                return font
            except Exception:
                continue

    font = ImageFont.load_default()
    _font_cache[key] = font
    return font


def _hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))


# ================================================================
#  DRAWING PRIMITIVES (design-aware)
# ================================================================


def _rounded_rectangle_mask(size, radius):
    """Return an alpha mask for a rounded rectangle."""
    w, h = size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius, fill=255)
    return mask


def _draw_geometric_elements(draw, theme, card_w, card_h):
    """Add subtle geometric accents that elevate the design."""
    t = theme

    if theme["name"] == "Geometric Silence":
        accent_y = int(card_h * 0.15)
        draw.rectangle(
            [0, accent_y, card_w, accent_y + 2], fill=t["divider"]
        )
        draw.rectangle(
            [t["card_padding"], card_h - t["card_padding"], t["card_padding"] + 32, card_h - t["card_padding"] + 2],
            fill=t["accent"],
        )

    elif theme["name"] == "Chromatic Systems":
        for i in range(6):
            x = t["card_padding"] + i * 12
            y = card_h - t["card_padding"]
            draw.rectangle([x, y - 2, x + 8, y], fill=t["accent"])

    elif theme["name"] == "Natural Clustering":
        cx, cy = t["card_padding"] - 10, card_h - t["card_padding"] + 10
        for r in range(20, 61, 20):
            draw.arc(
                [(cx - r, cy - r), (cx + r, cy + r)],
                start=180, end=270,
                fill=t["accent"], width=2,
            )

    elif theme["name"] == "Concrete Poetry":
        bar_y = int(card_h * 0.08)
        draw.rectangle([0, bar_y, card_w, bar_y + 6], fill=t["accent"])
        accent_x = int(card_w * 0.72)
        draw.rectangle(
            [accent_x, t["card_padding"], accent_x + 4, t["card_padding"] + 90],
            fill=t["accent_alt"],
        )


# ================================================================
#  LAYOUT ENGINE
# ================================================================


def _compute_layout(card_w, card_h, ui_w, ui_h, qr_size, padding):
    """
    Compute positions for every element so they sit comfortably
    with balanced spacing.  Returns a dict of (x, y, w, h).
    """
    inner_w = card_w - 2 * padding
    inner_h = card_h - 2 * padding
    gap = 28

    ui_area_x = padding
    ui_area_y = padding

    qr_area_x = card_w - padding - qr_size
    qr_area_y = card_h - padding - qr_size

    text_x = padding + ui_w + gap
    text_y = padding
    text_max_w = qr_area_x - text_x - gap
    return {
        "ui": {"x": ui_area_x, "y": ui_area_y, "w": ui_w, "h": ui_h},
        "qr": {"x": qr_area_x, "y": qr_area_y, "w": qr_size, "h": qr_size},
        "text": {"x": text_x, "y": text_y, "w": text_max_w, "h": inner_h},
        "inner": {"w": inner_w, "h": inner_h},
        "padding": padding,
        "gap": gap,
    }


def _text_block_height(draw, lines, font, line_spacing):
    h = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h += bbox[3] - bbox[1] + line_spacing
    return h


# ================================================================
#  MAIN CARD GENERATION
# ================================================================


def generate_card(
    url,
    model_name,
    ui_image_path,
    output_path="card.png",
    theme_name="minimal",
    subtitle="",
    accent_color_hex=None,
):
    theme = THEMES.get(theme_name, THEMES["minimal"])
    padding = theme["card_padding"]
    card_w, card_h = CARD_WIDTH, CARD_HEIGHT

    if accent_color_hex:
        theme["accent"] = _hex_to_rgb(accent_color_hex)

    # --- 1. Create canvas ---
    card = Image.new("RGB", (card_w, card_h), theme["bg"])
    draw = ImageDraw.Draw(card)

    # --- 2. Load & process UI image ---
    try:
        ui_img = Image.open(ui_image_path).convert("RGB")
    except Exception as e:
        print(f"[ERROR] Cannot read UI image: {e}")
        sys.exit(1)

    orig_w, orig_h = ui_img.size
    ratio = min(UI_MAX_WIDTH / orig_w, UI_MAX_HEIGHT / orig_h, 1.0)
    ui_w, ui_h = int(orig_w * ratio), int(orig_h * ratio)
    ui_img = ui_img.resize((ui_w, ui_h), Image.Resampling.LANCZOS)

    # Rounded corners for UI screenshot
    radius = theme["ui_border_radius"]
    mask = _rounded_rectangle_mask((ui_w, ui_h), radius)
    ui_rounded = Image.new("RGBA", (ui_w, ui_h), (0, 0, 0, 0))
    ui_rounded.paste(ui_img, (0, 0))
    ui_rounded.putalpha(mask)

    # Shadow behind UI
    shadow_offset = 6
    shadow = Image.new("RGBA", (ui_w + shadow_offset * 2, ui_h + shadow_offset * 2), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        [(shadow_offset, shadow_offset), (ui_w + shadow_offset - 1, ui_h + shadow_offset - 1)],
        radius=radius,
        fill=(0, 0, 0, 28),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))

    # --- 3. Compute layout ---
    layout = _compute_layout(card_w, card_h, ui_w, ui_h, QR_SIZE, padding)

    # --- 4. Paste UI with shadow ---
    u = layout["ui"]
    card.paste(shadow, (u["x"] - shadow_offset, u["y"] - shadow_offset), shadow)
    card.paste(ui_rounded, (u["x"], u["y"]), ui_rounded)

    # --- 5. Generate QR code ---
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    qr_img = qr_img.resize((QR_SIZE, QR_SIZE), Image.Resampling.LANCZOS)

    # QR with rounded corners and accent border
    qp = theme["qr_padding"]
    qr_outer = QR_SIZE + qp * 2
    qr_frame = Image.new("RGBA", (qr_outer, qr_outer), (0, 0, 0, 0))
    qr_frame_draw = ImageDraw.Draw(qr_frame)
    qr_frame_draw.rounded_rectangle(
        [(0, 0), (qr_outer - 1, qr_outer - 1)],
        radius=16, fill=(255, 255, 255, 255),
        outline=theme["accent"] + (255,), width=3,
    )
    qr_frame.paste(qr_img, (qp, qp), qr_img)

    q = layout["qr"]
    card.paste(qr_frame, (q["x"] - qp, q["y"] - qp), qr_frame)

    # --- 6. Typography ---
    ratio = theme["font_ratio"]
    font_heading = _resolve_font(36, prefer_bold=True)
    font_body = _resolve_font(int(36 * ratio["body"]))
    font_caption = _resolve_font(int(36 * ratio["caption"]))
    font_tag = _resolve_font(int(36 * ratio["body"]), prefer_bold=True)

    tx, ty = layout["text"]["x"], layout["text"]["y"]
    max_w = layout["text"]["w"]
    max_h = layout["text"]["h"]
    line_height = 18

    current_y = ty + 10

    # Tag badge
    tag = theme["name"].upper()
    tag_bbox = draw.textbbox((0, 0), tag, font=font_caption)
    tag_w = tag_bbox[2] - tag_bbox[0] + 20
    tag_h = tag_bbox[3] - tag_bbox[1] + 10
    draw.rounded_rectangle(
        [(tx, current_y), (tx + tag_w, current_y + tag_h)],
        radius=6,
        fill=theme["accent"],
        outline=None,
    )
    draw.text((tx + 10, current_y + 5), tag, fill=theme["bg"], font=font_caption)
    current_y += tag_h + 24

    # Divider line after tag
    draw.rectangle(
        [tx, current_y, tx + min(max_w, 60), current_y + 2],
        fill=theme["accent"],
    )
    current_y += 20

    # Model name
    draw.text((tx, current_y), model_name, fill=theme["text_primary"], font=font_heading)
    name_bbox = draw.textbbox((0, 0), model_name, font=font_heading)
    current_y += (name_bbox[3] - name_bbox[1]) + 12

    # Subtitle
    if subtitle:
        draw.text((tx, current_y), subtitle, fill=theme["text_secondary"], font=font_body)
        sub_bbox = draw.textbbox((0, 0), subtitle, font=font_body)
        current_y += (sub_bbox[3] - sub_bbox[1]) + 30
    else:
        current_y += 14

    # URL label
    url_label = "Scan to visit"
    draw.text((tx, current_y), url_label, fill=theme["text_secondary"], font=font_caption)
    current_y += 30

    # URL text
    display_url = url.replace("https://", "").replace("http://", "").rstrip("/")
    url_lines = []
    url_font = font_caption
    while display_url:
        for cut in reversed(range(1, min(len(display_url) + 1, 48))):
            bbox = draw.textbbox((0, 0), display_url[:cut], font=url_font)
            if bbox[2] - bbox[0] <= max_w:
                url_lines.append(display_url[:cut])
                display_url = display_url[cut:]
                break
        else:
            url_lines.append(display_url[:40])
            display_url = display_url[40:]

    for ul in url_lines[:2]:
        draw.text((tx, current_y), ul, fill=theme["accent"], font=url_font)
        current_y += 26

    # Bottom URL hint
    url_hint = url
    hint_font = _resolve_font(14)
    draw.text(
        (padding, card_h - padding - 18),
        url_hint,
        fill=theme["text_secondary"],
        font=hint_font,
    )

    # --- 7. Geometric design elements ---
    _draw_geometric_elements(draw, theme, card_w, card_h)

    # --- 8. Save ---
    card.save(output_path, "PNG", dpi=(300, 300))
    print(f"[OK] Card saved → {output_path}  (theme: {theme['name']})")


# ================================================================
#  CLI
# ================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate a design-forward shareable card with QR code.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_card.py --url https://example.com --name "Awesome Model" --image ui.png
  python generate_card.py --url https://example.com --name "Awesome Model" --image ui.png --theme tech
  python generate_card.py --url https://example.com --name "Awesome Model" --image ui.png --theme organic --subtitle "A next-gen AI assistant"
  python generate_card.py --url https://example.com --name "Awesome Model" --image ui.png --accent "#ff6b6b"

Available themes: minimal (default), tech, organic, bold
        """,
    )
    parser.add_argument("--url", required=True, help="Target URL (QR code destination)")
    parser.add_argument("--name", required=True, help="Model / product name")
    parser.add_argument("--image", required=True, help="Path to reference UI screenshot")
    parser.add_argument("--output", default="card.png", help="Output image path (default: card.png)")
    parser.add_argument(
        "--theme",
        choices=list(THEMES.keys()),
        default="minimal",
        help="Design theme (default: minimal)",
    )
    parser.add_argument("--subtitle", default="", help="Optional subtitle under model name")
    parser.add_argument("--accent", default=None, help="Override accent color (hex, e.g. #ff6b6b)")

    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"[ERROR] Image not found: {args.image}")
        sys.exit(1)

    generate_card(
        url=args.url,
        model_name=args.name,
        ui_image_path=args.image,
        output_path=args.output,
        theme_name=args.theme,
        subtitle=args.subtitle,
        accent_color_hex=args.accent,
    )


if __name__ == "__main__":
    main()
