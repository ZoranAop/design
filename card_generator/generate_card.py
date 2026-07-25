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

Dual rendering engines:
  - HTML/CSS + browser headless (primary, high fidelity)
  - Pillow/PIL card-in-canvas (fallback, no browser required)

14 design themes:
  - 4 canvas-design philosophies (minimal, tech, organic, bold)
  - 10 theme-factory palettes (tech-innovation, midnight-galaxy, ...)

3 output formats:
  - landscape  1200x630   (OG image / link preview)
  - social     800x1280   (portrait, WeChat / social sharing)
  - square     1080x1080  (1:1, Instagram feed)

Usage:
    python generate_card.py --url https://example.com --name "My Model" --image ui.png
    python generate_card.py --url https://example.com --name "My Model" --image ui.png --theme tech-innovation --format social
    python generate_card.py --url https://example.com --name "My Model" --image ui.png --renderer pillow
"""

import argparse
import base64
import io
import os
import shutil
import subprocess
import sys
import tempfile

import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor

# ================================================================
#  DESIGN THEMES
#  4 canvas-design philosophies + 10 theme-factory palettes
# ================================================================

THEMES = {
    # ---- canvas-design philosophies (original 4) ----
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
        "ui_radius": 16, "qr_radius": 14,
        "dark": False,
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
        "ui_radius": 12, "qr_radius": 12,
        "dark": True,
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
        "ui_radius": 20, "qr_radius": 16,
        "dark": False,
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
        "ui_radius": 8, "qr_radius": 8,
        "dark": True,
    },
    # ---- theme-factory palettes (10) ----
    "tech-innovation": {
        "name": "Tech Innovation",
        "canvas_bg": (10, 17, 23),
        "card_bg": (20, 30, 40),
        "text_primary": (255, 255, 255),
        "text_secondary": (139, 148, 158),
        "accent": (0, 102, 255),
        "accent_alt": (0, 255, 255),
        "divider": (48, 52, 61),
        "shadow_color": (0, 0, 0, 80),
        "ui_radius": 12, "qr_radius": 12,
        "dark": True,
    },
    "midnight-galaxy": {
        "name": "Midnight Galaxy",
        "canvas_bg": (26, 15, 46),
        "card_bg": (43, 30, 62),
        "text_primary": (230, 230, 250),
        "text_secondary": (164, 144, 194),
        "accent": (74, 78, 143),
        "accent_alt": (164, 144, 194),
        "divider": (61, 47, 92),
        "shadow_color": (0, 0, 0, 80),
        "ui_radius": 10, "qr_radius": 12,
        "dark": True,
    },
    "ocean-depths": {
        "name": "Ocean Depths",
        "canvas_bg": (13, 27, 42),
        "card_bg": (27, 73, 101),
        "text_primary": (202, 233, 255),
        "text_secondary": (95, 168, 211),
        "accent": (95, 168, 211),
        "accent_alt": (27, 73, 101),
        "divider": (27, 58, 92),
        "shadow_color": (0, 0, 0, 60),
        "ui_radius": 10, "qr_radius": 12,
        "dark": True,
    },
    "sunset-boulevard": {
        "name": "Sunset Boulevard",
        "canvas_bg": (255, 245, 230),
        "card_bg": (255, 250, 240),
        "text_primary": (92, 46, 14),
        "text_secondary": (194, 65, 12),
        "accent": (255, 107, 53),
        "accent_alt": (253, 200, 48),
        "divider": (254, 215, 170),
        "shadow_color": (60, 30, 10, 30),
        "ui_radius": 12, "qr_radius": 12,
        "dark": False,
    },
    "forest-canopy": {
        "name": "Forest Canopy",
        "canvas_bg": (27, 67, 50),
        "card_bg": (45, 106, 79),
        "text_primary": (216, 243, 220),
        "text_secondary": (149, 213, 178),
        "accent": (149, 213, 178),
        "accent_alt": (82, 183, 136),
        "divider": (45, 90, 61),
        "shadow_color": (0, 0, 0, 60),
        "ui_radius": 14, "qr_radius": 12,
        "dark": True,
    },
    "modern-minimalist": {
        "name": "Modern Minimalist",
        "canvas_bg": (245, 245, 245),
        "card_bg": (255, 255, 255),
        "text_primary": (26, 26, 26),
        "text_secondary": (108, 108, 108),
        "accent": (51, 51, 51),
        "accent_alt": (153, 153, 153),
        "divider": (208, 208, 208),
        "shadow_color": (0, 0, 0, 30),
        "ui_radius": 8, "qr_radius": 14,
        "dark": False,
    },
    "golden-hour": {
        "name": "Golden Hour",
        "canvas_bg": (92, 61, 46),
        "card_bg": (139, 94, 60),
        "text_primary": (255, 248, 220),
        "text_secondary": (212, 160, 23),
        "accent": (244, 196, 48),
        "accent_alt": (212, 160, 23),
        "divider": (107, 76, 46),
        "shadow_color": (0, 0, 0, 70),
        "ui_radius": 12, "qr_radius": 12,
        "dark": True,
    },
    "arctic-frost": {
        "name": "Arctic Frost",
        "canvas_bg": (232, 244, 248),
        "card_bg": (255, 255, 255),
        "text_primary": (28, 61, 90),
        "text_secondary": (70, 130, 180),
        "accent": (70, 130, 180),
        "accent_alt": (176, 224, 230),
        "divider": (192, 216, 232),
        "shadow_color": (28, 61, 90, 25),
        "ui_radius": 12, "qr_radius": 14,
        "dark": False,
    },
    "desert-rose": {
        "name": "Desert Rose",
        "canvas_bg": (245, 230, 230),
        "card_bg": (255, 245, 245),
        "text_primary": (90, 62, 62),
        "text_secondary": (139, 111, 111),
        "accent": (201, 160, 160),
        "accent_alt": (139, 111, 111),
        "divider": (220, 202, 202),
        "shadow_color": (90, 62, 62, 25),
        "ui_radius": 14, "qr_radius": 14,
        "dark": False,
    },
    "botanical-garden": {
        "name": "Botanical Garden",
        "canvas_bg": (240, 255, 240),
        "card_bg": (255, 255, 255),
        "text_primary": (45, 74, 45),
        "text_secondary": (74, 124, 74),
        "accent": (74, 124, 74),
        "accent_alt": (143, 188, 143),
        "divider": (192, 220, 192),
        "shadow_color": (45, 74, 45, 25),
        "ui_radius": 14, "qr_radius": 14,
        "dark": False,
    },
}

# ================================================================
#  FORMAT PRESETS
# ================================================================

FORMATS = {
    "landscape": {"w": 1200, "h": 630},
    "social": {"w": 800, "h": 1280},
    "square": {"w": 1080, "h": 1080},
}

CARD_MARGIN = 28
CARD_RADIUS = 20
CARD_PAD = 48
SHADOW_BLUR = 20
SHADOW_OFFSET = (4, 8)

# ================================================================
#  COLOR / ASSET UTILITIES
# ================================================================


def _hex_to_rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb[:3])


def _image_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _generate_qr_b64(url, box_size=10, border=1):
    qr = qrcode.QRCode(box_size=box_size, border=border)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


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


# ================================================================
#  BROWSER DETECTION
# ================================================================

_BROWSER_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/microsoft-edge", "/usr/bin/microsoft-edge-stable",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium", "/usr/bin/chromium-browser",
]


def find_browser():
    for path in _BROWSER_PATHS:
        if os.path.exists(path):
            return path
    for name in ["msedge", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
        found = shutil.which(name)
        if found:
            return found
    return None


# ================================================================
#  HTML TEMPLATE BUILDER
# ================================================================


def _build_html(url, name, logo_b64, qr_b64, theme, fmt, subtitle, accent_hex):
    t = dict(theme)
    if accent_hex:
        t["accent"] = _hex_to_rgb(accent_hex)

    w, h = fmt["w"], fmt["h"]
    is_portrait = h > w
    is_square = h == w

    canvas_hex = _rgb_to_hex(t["canvas_bg"])
    card_hex = _rgb_to_hex(t["card_bg"])
    text_hex = _rgb_to_hex(t["text_primary"])
    text_sec_hex = _rgb_to_hex(t["text_secondary"])
    accent_hex_val = _rgb_to_hex(t["accent"])
    accent_alt_hex = _rgb_to_hex(t["accent_alt"])
    divider_hex = _rgb_to_hex(t["divider"])

    name_size = 80 if is_portrait else (64 if is_square else 48)
    sub_size = 26 if is_portrait else (20 if is_square else 22)
    logo_box = 80 if is_portrait else (68 if is_square else 56)
    qr_box = 200 if is_portrait else (180 if is_square else 140)
    padding = "60px 50px" if is_portrait else ("50px" if is_square else "40px")

    display_url = url.replace("https://", "").replace("http://", "").rstrip("/")
    body_layout = "flex-direction:column;" if is_portrait else "flex-direction:row;"
    footer_layout = ("flex-direction:column; gap:24px; align-items:center;"
                     if is_portrait else
                     "flex-direction:row; justify-content:space-between; align-items:flex-end;")

    return f"""<!DOCTYPE html>
<html lang="zh">
<head><meta charset="UTF-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:{w}px; height:{h}px;
  font-family:'Inter','Segoe UI','Microsoft YaHei',sans-serif;
  background:{canvas_hex}; overflow:hidden; position:relative;
}}
.card {{
  width:calc(100% - 56px); height:calc(100% - 56px);
  margin:28px; border-radius:20px;
  background:{card_hex};
  {'background:linear-gradient(160deg,' + card_hex + ' 0%, ' + canvas_hex + ' 100%);' if t['dark'] else ''}
  box-shadow:0 8px 40px rgba(0,0,0,{'0.3' if t['dark'] else '0.1'});
  display:flex; {body_layout}
  padding:{padding}; position:relative; overflow:hidden;
}}
.card::before {{
  content:''; position:absolute; inset:0;
  background-image:
    linear-gradient({accent_hex_val}0a 1px, transparent 1px),
    linear-gradient(90deg, {accent_hex_val}0a 1px, transparent 1px);
  background-size:40px 40px; pointer-events:none;
}}
.card::after {{
  content:''; position:absolute; top:0; left:0; right:0; height:4px;
  background:linear-gradient(90deg, {accent_hex_val}, {accent_alt_hex}, {accent_hex_val});
}}
.header {{ display:flex; align-items:center; gap:18px; position:relative; z-index:2; }}
.logo-wrap {{
  width:{logo_box}px; height:{logo_box}px;
  background:rgba(255,255,255,{'0.08' if t['dark'] else '0.6'});
  border:1px solid {accent_hex_val}4d; border-radius:18px;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:blur(10px); flex-shrink:0;
}}
.logo-wrap img {{ width:60%; height:60%; object-fit:contain; }}
.brand {{ font-size:22px; font-weight:600; color:{text_hex}; letter-spacing:1px; }}
.brand-sub {{ font-size:12px; color:{text_sec_hex}; margin-top:3px; letter-spacing:2px; }}
.hero {{ flex:1; display:flex; flex-direction:column; justify-content:center; position:relative; z-index:2; }}
.tag {{
  display:inline-flex; align-items:center; gap:8px;
  background:{accent_hex_val}1f; border:1px solid {accent_hex_val}66;
  border-radius:30px; padding:6px 16px; font-size:13px;
  color:{accent_alt_hex}; font-weight:600; letter-spacing:1px;
  margin-bottom:20px; width:fit-content;
}}
.tag-dot {{ width:8px; height:8px; border-radius:50%; background:{accent_alt_hex}; box-shadow:0 0 12px {accent_alt_hex}; }}
.model-name {{
  font-size:{name_size}px; font-weight:900;
  {'background:linear-gradient(135deg,' + text_hex + ' 0%, ' + accent_alt_hex + ' 50%, ' + accent_hex_val + ' 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;' if t['dark'] else 'color:' + text_hex + ';'}
  letter-spacing:-2px; line-height:1.05; margin-bottom:10px;
}}
.subtitle {{ font-size:{sub_size}px; color:{text_sec_hex}; margin-bottom:14px; }}
.desc {{ font-size:16px; color:{text_sec_hex}; line-height:1.7; max-width:500px; }}
.footer {{
  display:flex; {footer_layout}
  position:relative; z-index:2; padding-top:24px;
  border-top:1px solid {divider_hex}; width:100%;
}}
.scan-hint {{ font-size:14px; color:{text_sec_hex}; margin-bottom:5px; letter-spacing:1px; }}
.url-text {{ font-size:18px; color:{accent_hex_val}; font-weight:600; font-family:'Courier New',monospace; }}
.url-text span {{ color:{accent_alt_hex}; }}
.qr-section {{ display:flex; flex-direction:column; align-items:center; gap:8px; }}
.qr-wrap {{
  width:{qr_box}px; height:{qr_box}px;
  background:rgba(255,255,255,{'0.05' if t['dark'] else '0.7'});
  border:2px solid {accent_hex_val}80; border-radius:20px; padding:12px;
  backdrop-filter:blur(10px); box-shadow:0 0 30px {accent_hex_val}33;
}}
.qr-wrap img {{ width:100%; height:100%; border-radius:8px; }}
.qr-label {{ font-size:12px; color:{text_sec_hex}; letter-spacing:2px; }}
.corner {{ position:absolute; width:40px; height:40px; border:2px solid {accent_hex_val}4d; z-index:1; }}
.corner.tl {{ top:14px; left:14px; border-right:none; border-bottom:none; border-radius:8px 0 0 0; }}
.corner.tr {{ top:14px; right:14px; border-left:none; border-bottom:none; border-radius:0 8px 0 0; }}
.corner.bl {{ bottom:14px; left:14px; border-right:none; border-top:none; border-radius:0 0 0 8px; }}
.corner.br {{ bottom:14px; right:14px; border-left:none; border-top:none; border-radius:0 0 8px 0; }}
</style></head>
<body>
<div class="card">
  <div class="corner tl"></div><div class="corner tr"></div>
  <div class="corner bl"></div><div class="corner br"></div>
  <div class="header">
    <div class="logo-wrap"><img src="data:image/png;base64,{logo_b64}" alt="logo"></div>
    <div><div class="brand">OPE.AI</div><div class="brand-sub">AI MODEL PLATFORM</div></div>
  </div>
  <div class="hero">
    <div class="tag"><span class="tag-dot"></span>NEW MODEL RELEASED</div>
    <div class="model-name">{name}</div>
    <div class="subtitle">{subtitle or 'Now Available'}</div>
    <div class="desc">Scan the QR code to visit the model page and start exploring.</div>
  </div>
  <div class="footer">
    <div class="footer-left">
      <div class="scan-hint">SCAN TO VISIT</div>
      <div class="url-text"><span>https://</span>{display_url}</div>
    </div>
    <div class="qr-section">
      <div class="qr-wrap"><img src="data:image/png;base64,{qr_b64}" alt="QR"></div>
      <div class="qr-label">SCAN ME</div>
    </div>
  </div>
</div>
</body></html>"""


# ================================================================
#  HTML RENDERER (browser headless)
# ================================================================


def _render_html(browser_path, html_str, output_path, width, height):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_str)
        html_path = f.name
    try:
        file_uri = "file:///" + html_path.replace("\\", "/")
        cmd = [browser_path, "--headless", "--disable-gpu", "--no-sandbox",
               "--hide-scrollbars", "--force-device-scale-factor=1",
               f"--window-size={width},{height}", f"--screenshot={output_path}", file_uri]
        subprocess.run(cmd, capture_output=True, timeout=30)
        return os.path.exists(output_path)
    finally:
        os.unlink(html_path)


# ================================================================
#  DRAWING PRIMITIVES (Pillow)
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
        radius=radius, fill=shadow_color,
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
    block = Image.new("RGBA", (outer + 60, outer + 20), (0, 0, 0, 0))
    bd = ImageDraw.Draw(block)
    bd.rounded_rectangle(
        [(0, 22), (outer - 1, outer + 22 - 1)],
        radius=theme["qr_radius"], fill=(255, 255, 255, 255),
        outline=theme["accent"] + (255,), width=2,
    )
    block.paste(qr_img, (pad, pad + 22), qr_img)
    bd.rectangle([4, 0, 4 + 32, 3], fill=theme["accent"])
    return block


def _draw_accent_dot(draw, x, y, color, r=3):
    draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=color)


# ================================================================
#  PILLOW RENDERER (card-in-canvas design)
# ================================================================


def _render_pillow(url, name, image_path, output_path, theme, fmt, subtitle, accent_hex):
    t = dict(theme)
    if accent_hex:
        t["accent"] = _hex_to_rgb(accent_hex)

    cw, ch = fmt["w"], fmt["h"]
    is_portrait = ch > cw

    canvas = Image.new("RGB", (cw, ch), t["canvas_bg"])
    draw = ImageDraw.Draw(canvas)

    card_margin = CARD_MARGIN
    card_x, card_y = card_margin, card_margin
    card_w = cw - card_margin * 2
    card_h = ch - card_margin * 2

    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([(0, 0), (card_w - 1, card_h - 1)], radius=CARD_RADIUS, fill=t["card_bg"])

    pad = CARD_PAD
    ui_max_w = min(520, card_w - 2 * pad - 200)
    ui_max_h = min(340, card_h - 2 * pad - 100)
    qr_size = 140 if not is_portrait else 160

    if is_portrait:
        left_x = pad
        left_w = card_w - pad * 2
        left_h = card_h - pad * 2
        gap = 0
        right_x = pad
        right_w = card_w - pad * 2
    else:
        left_x = pad
        left_w = ui_max_w
        left_h = card_h - pad * 2
        gap = 48
        right_x = left_x + left_w + gap
        right_w = card_w - right_x - pad

    # UI image
    ui_img = Image.open(image_path).convert("RGB")
    ow, oh = ui_img.size
    scale = min(ui_max_w / ow, ui_max_h / oh, 1.0)
    uw, uh = int(ow * scale), int(oh * scale)
    ui_img = ui_img.resize((uw, uh), Image.Resampling.LANCZOS)

    if is_portrait:
        ui_y = pad
        ui_x = left_x + (left_w - uw) // 2
    else:
        ui_y = pad + (left_h - uh) // 2
        ui_x = left_x

    mask = _rounded_mask((uw, uh), t["ui_radius"])
    ui_rounded = Image.new("RGBA", (uw, uh), (0, 0, 0, 0))
    ui_rounded.paste(ui_img, (0, 0))
    ui_rounded.putalpha(mask)

    ushadow = Image.new("RGBA", (uw + 20, uh + 20), (0, 0, 0, 30))
    ushadow = ushadow.filter(ImageFilter.GaussianBlur(radius=10))
    card.paste(ushadow, (ui_x - 4, ui_y + 4), ushadow)
    card.paste(ui_rounded, (ui_x, ui_y), ui_rounded)
    cd.rounded_rectangle(
        [(ui_x - 1, ui_y - 1), (ui_x + uw, ui_y + uh)],
        radius=t["ui_radius"], outline=t["divider"], width=1,
    )

    # QR block
    qr_block = _make_qr_block(url, qr_size, t)
    qr_bw, qr_bh = qr_block.size

    # Typography
    heading_font = _resolve_font(48 if not is_portrait else 56, prefer_bold=True)
    body_font = _resolve_font(22 if not is_portrait else 26)
    caption_font = _resolve_font(16 if not is_portrait else 18)

    display_url = url.replace("https://", "").replace("http://", "").rstrip("/")

    lines_info = []

    # Model name (may need wrapping)
    remaining = name
    while remaining:
        for cut in range(len(remaining), 0, -1):
            if draw.textlength(remaining[:cut], font=heading_font) <= right_w:
                lines_info.append(("heading", remaining[:cut], heading_font))
                remaining = remaining[cut:]
                break
        else:
            lines_info.append(("heading", remaining, heading_font))
            break

    if subtitle:
        lines_info.append(("gap_small", "", None))
        lines_info.append(("body", subtitle, body_font))
    lines_info.append(("gap_big", "", None))
    lines_info.append(("caption", "扫码访问", caption_font))

    # URL wrapping
    display_url_copy = display_url
    while display_url_copy:
        for cut in range(min(len(display_url_copy), 40), 0, -1):
            if draw.textlength(display_url_copy[:cut], font=caption_font) <= right_w - 10:
                lines_info.append(("url", display_url_copy[:cut], caption_font))
                display_url_copy = display_url_copy[cut:]
                break
        else:
            lines_info.append(("url", display_url_copy[:40], caption_font))
            display_url_copy = display_url_copy[40:]

    lines_info.append(("qr_gap", "", None))
    lines_info.append(("qr", "", None))

    text_h = 0
    for kind, _, _ in lines_info:
        if kind == "gap_small": text_h += 12
        elif kind == "gap_big": text_h += 24
        elif kind == "qr_gap": text_h += 16
        elif kind == "qr": text_h += qr_bh
        elif kind == "caption": text_h += 26
        elif kind == "body": text_h += 30
        elif kind == "heading": text_h += 56
    text_h -= 8

    section_y = pad + (left_h - text_h) // 2 if not is_portrait else pad + uh + 40
    draw_y = section_y
    for kind, content, font in lines_info:
        if kind == "heading" and font:
            cd.text((right_x, draw_y), content, fill=t["text_primary"], font=font)
            draw_y += 56
        elif kind == "body" and font:
            cd.text((right_x, draw_y), content, fill=t["text_secondary"], font=font)
            draw_y += 30
        elif kind == "caption" and font:
            cd.text((right_x, draw_y), content, fill=t["text_secondary"], font=font)
            draw_y += 26
        elif kind == "gap_small": draw_y += 12
        elif kind == "gap_big": draw_y += 24
        elif kind == "qr_gap": draw_y += 16
        elif kind == "qr":
            qr_paste_x = right_x + (right_w - qr_bw) // 2
            card.paste(qr_block, (qr_paste_x, draw_y - 2), qr_block)
            draw_y += qr_bh

    # Decorative elements
    cd.rectangle([(pad, card_h - pad - 1), (pad + 40, card_h - pad)], fill=t["accent"])
    _draw_accent_dot(cd, card_w - pad, pad, t["accent"], 4)
    _draw_accent_dot(cd, card_w - pad - 18, pad, t["accent_alt"], 3)

    # Shadow + paste
    card_with_shadow = _draw_shadow(card, CARD_RADIUS, t["shadow_color"], SHADOW_OFFSET, SHADOW_BLUR)
    paste_x = card_x - SHADOW_BLUR
    paste_y = card_y - SHADOW_BLUR
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(card_with_shadow, (paste_x, paste_y), card_with_shadow)

    canvas_draw = ImageDraw.Draw(canvas_rgba)
    canvas_draw.rectangle([card_margin, ch - 1, cw - card_margin, ch], fill=t["divider"])

    canvas_rgba.convert("RGB").save(output_path, "PNG", dpi=(300, 300))
    return True


# ================================================================
#  MAIN ORCHESTRATOR
# ================================================================


def generate_card(url, name, image_path, output_path="card.png",
                  theme="tech-innovation", subtitle="", accent_hex=None,
                  fmt_name="landscape", renderer="auto"):
    t = THEMES.get(theme, THEMES["tech-innovation"])
    fmt = FORMATS.get(fmt_name, FORMATS["landscape"])

    if not os.path.exists(image_path):
        print(f"[ERROR] Image not found: {image_path}")
        sys.exit(1)

    use_html = renderer in ("html", "auto")
    browser = find_browser() if use_html else None

    if browser and renderer in ("html", "auto"):
        logo_b64 = _image_to_b64(image_path)
        qr_b64 = _generate_qr_b64(url)
        html_str = _build_html(url, name, logo_b64, qr_b64, t, fmt, subtitle, accent_hex)
        ok = _render_html(browser, html_str, output_path, fmt["w"], fmt["h"])
        if ok:
            print(f"[OK] Card saved -> {output_path}  "
                  f"(theme: {t['name']}, format: {fmt_name}, "
                  f"renderer: html/{os.path.basename(browser)})")
            return
        print("[WARN] HTML render failed, falling back to Pillow...")

    _render_pillow(url, name, image_path, output_path, t, fmt, subtitle, accent_hex)
    print(f"[OK] Card saved -> {output_path}  "
          f"(theme: {t['name']}, format: {fmt_name}, renderer: pillow)")


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
  python generate_card.py --url https://example.com --name "Model" --image ui.png --theme tech-innovation --format social
  python generate_card.py --url https://example.com --name "Model" --image ui.png --renderer pillow
  python generate_card.py --url https://example.com --name "Model" --image ui.png --theme midnight-galaxy --subtitle "Now Available" --accent "#ff6b6b"

Available themes: """ + ", ".join(THEMES.keys()) + """

Available formats: landscape (1200x630), social (800x1280), square (1080x1080)
Available renderers: auto (default), html, pillow
        """,
    )
    parser.add_argument("--url", required=True, help="Target URL (QR code destination)")
    parser.add_argument("--name", required=True, help="Model / product name")
    parser.add_argument("--image", required=True, help="Path to reference UI screenshot / logo")
    parser.add_argument("--output", default="card.png", help="Output image path")
    parser.add_argument("--theme", choices=list(THEMES.keys()), default="tech-innovation")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--accent", default=None, help="Override accent color (hex)")
    parser.add_argument("--format", choices=list(FORMATS.keys()), default="landscape",
                        help="Output format (default: landscape)")
    parser.add_argument("--renderer", choices=["auto", "html", "pillow"], default="auto",
                        help="Rendering engine (default: auto)")

    args = parser.parse_args()

    generate_card(
        url=args.url, name=args.name, image_path=args.image,
        output_path=args.output, theme=args.theme, subtitle=args.subtitle,
        accent_hex=args.accent, fmt_name=args.format, renderer=args.renderer,
    )


if __name__ == "__main__":
    main()
