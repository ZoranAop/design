#!/usr/bin/env python3
"""
============================================================
 Card Generator  --  Design-forward shareable card creator
============================================================

Generates a visually polished share card with QR code.
Design philosophy: magazine-editorial quality. Every element
is placed with painstaking attention to spacing, balance,
and visual rhythm. The result should feel like a curated
artifact — not a utility layout.

Usage:
    python generate_card.py --url https://example.com --name "My Model" --image ui.png
    python generate_card.py --url https://example.com --name "My Model" --image ui.png --theme tech
"""

import argparse
import os
import sys
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor

# ================================================================
#  DESIGN THEMES
# ================================================================

THEMES = {
    "minimal": {
        "name": "Geometric Silence",
        "canvas_bg": (242, 241, 238),
        "card_bg": (255, 255, 255),
        "text_primary": (20, 20, 19),
        "text_secondary": (130, 125, 115),
        "accent": (140, 156, 118),
        "accent_alt": (176, 174, 165),
        "divider": (232, 230, 220),
        "shadow_color": (0, 0, 0, 40),
        "ui_radius": 16,
        "qr_radius": 14,
    },
    "tech": {
        "name": "Chromatic Systems",
        "canvas_bg": (10, 12, 20),
        "card_bg": (20, 24, 35),
        "text_primary": (235, 240, 248),
        "text_secondary": (120, 130, 150),
        "accent": (88, 166, 255),
        "accent_alt": (63, 185, 80),
        "divider": (40, 46, 58),
        "shadow_color": (0, 0, 0, 80),
        "ui_radius": 12,
        "qr_radius": 12,
    },
    "organic": {
        "name": "Natural Clustering",
        "canvas_bg": (242, 236, 225),
        "card_bg": (255, 252, 245),
        "text_primary": (50, 40, 30),
        "text_secondary": (140, 115, 90),
        "accent": (217, 119, 87),
        "accent_alt": (120, 140, 93),
        "divider": (230, 220, 205),
        "shadow_color": (60, 40, 20, 30),
        "ui_radius": 20,
        "qr_radius": 16,
    },
    "bold": {
        "name": "Concrete Poetry",
        "canvas_bg": (14, 14, 14),
        "card_bg": (24, 24, 24),
        "text_primary": (252, 250, 245),
        "text_secondary": (180, 175, 165),
        "accent": (230, 125, 80),
        "accent_alt": (106, 155, 204),
        "divider": (50, 48, 45),
        "shadow_color": (0, 0, 0, 100),
        "ui_radius": 8,
        "qr_radius": 8,
    },
}

CANVAS_W, CANVAS_H = 1200, 630
CARD_MARGIN = 28
CARD_RADIUS = 20
CARD_PAD = 48
UI_MAX_W, UI_MAX_H = 520, 340
QR_SIZE = 140
SHADOW_BLUR = 20
SHADOW_OFFSET = (4, 8)


# ================================================================
#  FONT HELPERS
# ================================================================

_font_cache = {}


def _resolve_font(size, prefer_bold=False):
    key = (size, prefer_bold)
    if key in _font_cache:
        return _font_cache[key]

    if prefer_bold:
        candidates = ["segoeuib.ttf", "seguisb.ttf", "msyhbd.ttf", "simhei.ttf", "arialbd.ttf", "arial.ttf"]
    else:
        candidates = ["segoeui.ttf", "segoe.ttf", "msyh.ttc", "msyh.ttf", "simhei.ttf", "arial.ttf"]

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


def _hex_to_rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


# ================================================================
#  DRAWING PRIMITIVES
# ================================================================


def _rounded_mask(size, radius):
    w, h = size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius, fill=255)
    return mask


def _draw_shadow(card_img, radius, shadow_color, shadow_offset, shadow_blur):
    cw, ch = card_img.size
    pad = shadow_blur * 2
    sw, sh = cw + pad, ch + pad
    shadow = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        [(shadow_blur + shadow_offset[0], shadow_blur + shadow_offset[1]),
         (cw + shadow_blur + shadow_offset[0] - 1, ch + shadow_blur + shadow_offset[1] - 1)],
        radius=radius,
        fill=shadow_color,
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))

    canvas = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    canvas.paste(shadow, (0, 0), shadow)
    canvas.paste(card_img.convert("RGBA"), (shadow_blur, shadow_blur), card_img)
    return canvas


def _make_qr_block(url, size, theme):
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)

    pad = 12
    outer = size + pad * 2
    block = Image.new("RGBA", (outer + 60, outer + 20), (0, 0, 0, 0))  # +60 for text, +20 for accent bar
    bd = ImageDraw.Draw(block)

    bd.rounded_rectangle(
        [(0, 22), (outer - 1, outer + 22 - 1)],
        radius=theme["qr_radius"],
        fill=(255, 255, 255, 255),
        outline=theme["accent"] + (255,),
        width=2,
    )
    block.paste(qr_img, (pad, pad + 22), qr_img)

    # Accent bar above QR
    bd.rectangle([4, 0, 4 + 32, 3], fill=theme["accent"])

    return block


def _draw_accent_dot(draw, x, y, color, r=3):
    draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)


# ================================================================
#  MAIN CARD GENERATION
# ================================================================


def generate_card(url, name, image_path, output_path, theme="minimal", subtitle=""):
    t = THEMES[theme]
    cw, ch = CANVAS_W, CANVAS_H

    # === Canvas background ===
    canvas = Image.new("RGB", (cw, ch), t["canvas_bg"])
    draw = ImageDraw.Draw(canvas)

    # === The card (centered white block) ===
    card_margin = CARD_MARGIN
    card_x, card_y = card_margin, card_margin
    card_w = cw - card_margin * 2
    card_h = ch - card_margin * 2

    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)

    # Card background with rounded corners
    cd.rounded_rectangle(
        [(0, 0), (card_w - 1, card_h - 1)],
        radius=CARD_RADIUS,
        fill=t["card_bg"],
    )

    # === Card interior layout ===
    pad = CARD_PAD
    left_x = pad
    left_w = UI_MAX_W
    left_h = card_h - pad * 2

    # Gap between left (UI) and right (text + QR)
    gap = 48
    right_x = left_x + left_w + gap
    right_w = card_w - right_x - pad

    # === UI Screenshot ===
    ui_img = Image.open(image_path).convert("RGB")
    ow, oh = ui_img.size
    scale = min(UI_MAX_W / ow, UI_MAX_H / oh, 1.0)
    uw, uh = int(ow * scale), int(oh * scale)
    ui_img = ui_img.resize((uw, uh), Image.Resampling.LANCZOS)

    # Centered vertically in left column
    ui_y = pad + (left_h - uh) // 2

    # Rounded + shadow
    mask = _rounded_mask((uw, uh), t["ui_radius"])
    ui_rounded = Image.new("RGBA", (uw, uh), (0, 0, 0, 0))
    ui_rounded.paste(ui_img, (0, 0))
    ui_rounded.putalpha(mask)

    # Small shadow under UI
    ushadow = Image.new("RGBA", (uw + 20, uh + 20), (0, 0, 0, 30))
    ushadow = ushadow.filter(ImageFilter.GaussianBlur(radius=10))
    card.paste(ushadow, (left_x - 4, ui_y + 4), ushadow)
    card.paste(ui_rounded, (left_x, ui_y), ui_rounded)

    # Thin border around UI
    cd.rounded_rectangle(
        [(left_x - 1, ui_y - 1), (left_x + uw, ui_y + uh)],
        radius=t["ui_radius"],
        outline=t["divider"],
        width=1,
    )

    # === QR block ===
    qr_block = _make_qr_block(url, QR_SIZE, t)
    qr_bw, qr_bh = qr_block.size

    # === Typography (right column) ===
    # Vertical centering of text + QR
    heading_font = _resolve_font(48, prefer_bold=True)
    body_font = _resolve_font(22)
    caption_font = _resolve_font(16)

    display_url = url.replace("https://", "").replace("http://", "").rstrip("/")

    # Measure text block height
    lines_info = []

    # Model name (may need wrapping)
    name_lines = []
    remaining = name
    while remaining:
        for cut in range(len(remaining), 0, -1):
            w = draw.textlength(remaining[:cut], font=heading_font)
            if w <= right_w:
                name_lines.append(remaining[:cut])
                remaining = remaining[cut:]
                break
        else:
            name_lines.append(remaining)
            break

    for ln in name_lines:
        lines_info.append(("heading", ln, heading_font))

    # Subtitle
    if subtitle:
        lines_info.append(("gap_small", "", None))
        lines_info.append(("body", subtitle, body_font))

    # Gap before URL section
    lines_info.append(("gap_big", "", None))

    # "Scan to visit" label
    lines_info.append(("caption", "扫码访问", caption_font))

    # URL display
    url_parts = []
    display_url_copy = display_url
    while display_url_copy:
        for cut in range(min(len(display_url_copy), 40), 0, -1):
            w = draw.textlength(display_url_copy[:cut], font=caption_font)
            if w <= right_w - 10:
                url_parts.append(display_url_copy[:cut])
                display_url_copy = display_url_copy[cut:]
                break
        else:
            url_parts.append(display_url_copy[:40])
            display_url_copy = display_url_copy[40:]
    for up in url_parts[:2]:
        lines_info.append(("url", up, caption_font))

    # QR block
    lines_info.append(("qr_gap", "", None))
    lines_info.append(("qr", "", None))

    # Compute total text height
    text_h = 0
    for kind, _, font in lines_info:
        if kind in ("gap_small",):
            text_h += 12
        elif kind in ("gap_big",):
            text_h += 24
        elif kind in ("qr_gap",):
            text_h += 16
        elif kind == "qr":
            text_h += qr_bh
        elif kind == "caption":
            text_h += 26
        elif kind == "url":
            text_h += 24
        elif kind == "body":
            text_h += 30
        elif kind == "heading":
            text_h += 56
    text_h -= 8  # last line compensation

    # Compute starting Y for vertical centering
    section_y = pad + (left_h - text_h) // 2

    # Draw text
    draw_y = section_y
    for kind, content, font in lines_info:
        if kind == "heading":
            card_draw = cd
            draw_draw = draw
            tx = right_x
            color = t["text_primary"]
            if font:
                card_draw.text((tx, draw_y), content, fill=color, font=font)
            draw_y += 56
        elif kind == "body":
            card_draw = cd
            draw_draw = draw
            if font:
                card_draw.text((right_x, draw_y), content, fill=t["text_secondary"], font=font)
            draw_y += 30
        elif kind in ("caption",):
            if font:
                cd.text((right_x, draw_y), content, fill=t["text_secondary"], font=font)
            draw_y += 26
        elif kind == "url":
            if font:
                cd.text((right_x, draw_y), content, fill=t["accent"], font=font)
            draw_y += 24
        elif kind == "gap_small":
            draw_y += 12
        elif kind == "gap_big":
            draw_y += 24
        elif kind == "qr_gap":
            draw_y += 16
        elif kind == "qr":
            qr_paste_x = right_x + (right_w - qr_bw) // 2
            card.paste(qr_block, (qr_paste_x, draw_y - 2), qr_block)
            draw_y += qr_bh

    # === Subtle decorative elements on card ===
    # Bottom-left corner accent
    accent_x, accent_y_bot = pad, card_h - pad
    cd.rectangle(
        [(accent_x, accent_y_bot - 1), (accent_x + 40, accent_y_bot)],
        fill=t["accent"],
    )

    # Small dot accents scattered
    _draw_accent_dot(cd, card_w - pad, pad, t["accent"], 4)
    _draw_accent_dot(cd, card_w - pad - 18, pad, t["accent_alt"], 3)

    # === Shadow around card ===
    card_with_shadow = _draw_shadow(
        card, CARD_RADIUS, t["shadow_color"], SHADOW_OFFSET, SHADOW_BLUR
    )

    # === Paste card onto canvas ===
    paste_x = card_x - SHADOW_BLUR
    paste_y = card_y - SHADOW_BLUR
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(card_with_shadow, (paste_x, paste_y), card_with_shadow)

    # === Canvas-level decorative elements ===
    canvas_draw = ImageDraw.Draw(canvas_rgba)

    # Thin rule at bottom of canvas
    rule_y = ch - 1
    canvas_draw.rectangle([card_margin, rule_y, cw - card_margin, rule_y + 1], fill=t["divider"])

    # === Save ===
    canvas_rgba = canvas_rgba.convert("RGB")
    canvas_rgba.save(output_path, "PNG", dpi=(300, 300))
    print(f"[OK] Card saved → {output_path}  (theme: {t['name']})")


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
  python generate_card.py --url https://example.com --name "Model" --image ui.png --theme tech
  python generate_card.py --url https://example.com --name "Model" --image ui.png --theme organic --subtitle "Tagline here"

Available themes: minimal (default), tech, organic, bold
        """,
    )
    parser.add_argument("--url", required=True, help="Target URL (QR code destination)")
    parser.add_argument("--name", required=True, help="Model / product name")
    parser.add_argument("--image", required=True, help="Path to reference UI screenshot")
    parser.add_argument("--output", default="card.png", help="Output image path")
    parser.add_argument("--theme", choices=list(THEMES.keys()), default="minimal")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--accent", default=None, help="Override accent color (hex)")

    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"[ERROR] Image not found: {args.image}")
        sys.exit(1)

    t = THEMES[args.theme]
    if args.accent:
        t["accent"] = _hex_to_rgb(args.accent)

    generate_card(
        url=args.url,
        name=args.name,
        image_path=args.image,
        output_path=args.output,
        theme=args.theme,
        subtitle=args.subtitle,
    )


if __name__ == "__main__":
    main()
