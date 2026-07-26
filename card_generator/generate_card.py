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

Architecture:  skill  ->  tool call  ->  page generation
  - This file is the "tool call" layer (invoked by SKILL.md)
  - Themes are loaded from the shared ../themes.json (single
    source of truth, shared with the Node.js satori renderer)
  - Output images are the "page generation" layer

Renderers (all selectable via --renderer):
  - auto   : browser headless -> Pillow fallback
  - html   : force HTML/CSS + browser headless (high fidelity)
  - pillow : force Pillow/PIL card-in-canvas (no browser needed)
  - satori : delegate to Node.js satori-card/generate.js (subprocess)

Usage:
    python generate_card.py --url https://example.com --name "My Model" --image ui.png
    python generate_card.py --url https://example.com --name "My Model" --image ui.png --theme tech-innovation --format social
    python generate_card.py --url https://example.com --name "My Model" --image ui.png --renderer satori
"""

import argparse
import base64
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ================================================================
#  SHARED THEME LOADER  (single source of truth: themes.json)
# ================================================================

_HERE = os.path.dirname(os.path.abspath(__file__))
_THEMES_FILE = os.path.normpath(os.path.join(_HERE, "..", "themes.json"))


def _hex_to_rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def _load_themes():
    """Load themes from the shared themes.json and normalize to RGB tuples."""
    with open(_THEMES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    formats = data["formats"]
    themes = {}
    for key, t in data["themes"].items():
        c = t["colors"]
        sh = t["shadow"]
        themes[key] = {
            "name": t["name"],
            "category": t.get("category", ""),
            "mood": t.get("mood", ""),
            "canvas_bg": _hex_to_rgb(c["canvas_bg"]),
            "card_bg": _hex_to_rgb(c["card_bg"]),
            "text_primary": _hex_to_rgb(c["text_primary"]),
            "text_secondary": _hex_to_rgb(c["text_secondary"]),
            "accent": _hex_to_rgb(c["accent"]),
            "accent_alt": _hex_to_rgb(c["accent_alt"]),
            "divider": _hex_to_rgb(c["divider"]),
            "shadow_color": (sh["r"], sh["g"], sh["b"], sh["a"]),
            "ui_radius": t["ui_radius"],
            "qr_radius": t["qr_radius"],
            "dark": t["dark"],
        }
    return formats, themes


FORMATS, THEMES = _load_themes()

# ================================================================
#  LOCALE STRINGS  (unified per-card copy; international default = en)
# ================================================================

LOCALES = {
    "en": {
        "badge": "NEW RELEASE",
        "scan_hint": "SCAN TO VISIT",
        "scan_label": "SCAN ME",
        "default_subtitle": "Now Available",
    },
    "zh": {
        "badge": "全新发布",
        "scan_hint": "扫码访问",
        "scan_label": "扫一扫",
        "default_subtitle": "现已上线",
    },
    "zh-Hant": {
        "badge": "全新發佈",
        "scan_hint": "掃碼訪問",
        "scan_label": "掃一掃",
        "default_subtitle": "現已上線",
    },
    "ja": {
        "badge": "新登場",
        "scan_hint": "スキャンして開く",
        "scan_label": "スキャン",
        "default_subtitle": "提供開始",
    },
}


def _loc(lang):
    return LOCALES.get(lang, LOCALES["en"])


# ================================================================
#  LAYOUT CONSTANTS
# ================================================================

CARD_MARGIN = 28
CARD_RADIUS = 24
CARD_PAD = 56
SHADOW_BLUR = 24
SHADOW_OFFSET = (0, 10)

# ================================================================
#  COLOR / ASSET UTILITIES
# ================================================================


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


def _build_html(url, name, logo_b64, qr_b64, theme, fmt, subtitle, accent_hex,
                brand="", platform="", lang="en", features=None):
    """Clean, international, minimal card. Generous whitespace, one accent rule,
    clear hierarchy, subtle shadow. Layout adapts to landscape / social / square."""
    t = dict(theme)
    if accent_hex:
        t["accent"] = _hex_to_rgb(accent_hex)

    loc = _loc(lang)
    features = [f for f in (features or []) if f][:3]
    w, h = fmt["w"], fmt["h"]
    is_portrait = h > w
    is_square = h == w

    canvas_hex = _rgb_to_hex(t["canvas_bg"])
    card_hex = _rgb_to_hex(t["card_bg"])
    text_hex = _rgb_to_hex(t["text_primary"])
    text_sec_hex = _rgb_to_hex(t["text_secondary"])
    accent_hex_val = _rgb_to_hex(t["accent"])
    divider_hex = _rgb_to_hex(t["divider"])
    logo_bg = "rgba(255,255,255,0.04)" if t["dark"] else "rgba(0,0,0,0.02)"
    shadow = "0 16px 64px rgba(0,0,0,0.55)" if t["dark"] else "0 16px 64px rgba(0,0,0,0.08)"

    name_size = 66 if is_portrait else (56 if is_square else 46)
    sub_size = 22 if is_portrait else (20 if is_square else 19)
    logo_box = 132 if is_portrait else (150 if is_square else 120)
    qr_box = 132 if is_portrait else (150 if is_square else 108)
    pad = 64 if is_portrait else (60 if is_square else 56)

    display_url = url.replace("https://", "").replace("http://", "").rstrip("/")

    # Optional brand line (hidden if not provided)
    brand_html = ""
    if brand or platform:
        b = f'<div class="brand">{brand}</div>' if brand else ""
        p = f'<div class="platform">{platform}</div>' if platform else ""
        brand_html = f'<div class="brandblock">{b}{p}</div>'

    # Optional feature bullets (portrait/square only)
    features_html = ""
    if features:
        items = "".join(
            f'<div class="feat"><span class="feat-dot"></span>{f}</div>' for f in features
        )
        features_html = f'<div class="features">{items}</div>'

    # Layout: portrait/square = vertical centered; landscape = split row
    if is_portrait or is_square:
        body = f"""
  {brand_html}
  <div class="logo-wrap"><img src="data:image/png;base64,{logo_b64}" alt="logo"></div>
  <div class="badge">{loc['badge']}</div>
  <div class="name">{name}</div>
  <div class="subtitle">{subtitle or loc['default_subtitle']}</div>
  <div class="rule"></div>
  {features_html}
  <div class="spacer"></div>
  <div class="footer">
    <div class="qr-wrap"><img src="data:image/png;base64,{qr_b64}" alt="QR"></div>
    <div class="footer-text">
      <div class="scan-hint">{loc['scan_hint']}</div>
      <div class="url-text">{display_url}</div>
    </div>
  </div>"""
        card_layout = "flex-direction:column; align-items:center; text-align:center;"
        footer_layout = "flex-direction:row; align-items:center; justify-content:center; gap:22px;"
        name_align = "text-align:center;"
    else:
        body = f"""
  <div class="left">
    <div class="logo-wrap"><img src="data:image/png;base64,{logo_b64}" alt="logo"></div>
  </div>
  <div class="right">
    {brand_html}
    <div class="badge">{loc['badge']}</div>
    <div class="name">{name}</div>
    <div class="subtitle">{subtitle or loc['default_subtitle']}</div>
    <div class="rule"></div>
    <div class="footer">
      <div class="qr-wrap"><img src="data:image/png;base64,{qr_b64}" alt="QR"></div>
      <div class="footer-text">
        <div class="scan-hint">{loc['scan_hint']}</div>
        <div class="url-text">{display_url}</div>
      </div>
    </div>
  </div>"""
        card_layout = "flex-direction:row; align-items:stretch;"
        footer_layout = "flex-direction:row; align-items:center; gap:20px;"
        name_align = ""

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head><meta charset="UTF-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:{w}px; height:{h}px;
  font-family:'Inter','Segoe UI','Microsoft YaHei','PingFang SC',sans-serif;
  background:{canvas_hex}; overflow:hidden;
}}
.card {{
  width:calc(100% - 56px); height:calc(100% - 56px);
  margin:28px; border-radius:24px;
  background:{card_hex}; box-shadow:{shadow};
  display:flex; {card_layout}
  padding:{pad}px; overflow:hidden;
}}
.left {{ display:flex; align-items:center; justify-content:center; width:48%; padding-right:{pad//2}px; }}
.right {{ display:flex; flex-direction:column; justify-content:center; flex:1; }}
.brandblock {{ margin-bottom:24px; }}
.brand {{ font-size:18px; font-weight:600; color:{text_hex}; letter-spacing:0.3px; }}
.platform {{ font-size:12px; font-weight:600; color:{text_sec_hex}; text-transform:uppercase; letter-spacing:3px; margin-top:4px; }}
.logo-wrap {{
  width:{logo_box}px; height:{logo_box}px;
  background:{logo_bg}; border:1px solid {divider_hex}; border-radius:28px;
  display:flex; align-items:center; justify-content:center; padding:26px; flex-shrink:0;
}}
.logo-wrap img {{ max-width:100%; max-height:100%; object-fit:contain; }}
.badge {{
  display:inline-flex; align-self:{'center' if (is_portrait or is_square) else 'flex-start'};
  align-items:center; background:{accent_hex_val}1a; border:1px solid {accent_hex_val}55;
  border-radius:100px; padding:5px 16px; font-size:12px; font-weight:700;
  color:{accent_hex_val}; letter-spacing:2px; margin:{('28px 0 18px' if (is_portrait or is_square) else '0 0 20px')};
}}
.name {{
  font-size:{name_size}px; font-weight:700; color:{text_hex};
  letter-spacing:-1px; line-height:1.1; {name_align}
}}
.subtitle {{ font-size:{sub_size}px; font-weight:400; color:{text_sec_hex}; margin-top:12px; {name_align} }}
.rule {{ width:{'100px' if (is_portrait or is_square) else '64px'}; height:1px; background:{divider_hex}; margin-top:28px; }}
.features {{ display:flex; flex-direction:column; align-items:center; gap:14px; margin-top:28px; }}
.feat {{ display:flex; align-items:center; font-size:16px; font-weight:400; color:{text_sec_hex}; letter-spacing:0.3px; }}
.feat-dot {{ width:5px; height:5px; border-radius:3px; background:{accent_hex_val}; margin-right:14px; }}
.spacer {{ flex:1; }}
.footer {{ display:flex; {footer_layout} margin-top:28px; width:100%; }}
.qr-wrap {{
  width:{qr_box}px; height:{qr_box}px; background:#ffffff;
  border:1px solid {divider_hex}; border-radius:16px; padding:8px; flex-shrink:0;
}}
.qr-wrap img {{ width:100%; height:100%; }}
.footer-text {{ display:flex; flex-direction:column; text-align:left; }}
.scan-hint {{ font-size:12px; font-weight:600; color:{text_sec_hex}; text-transform:uppercase; letter-spacing:2px; margin-bottom:8px; }}
.url-text {{ font-size:16px; font-weight:500; color:{accent_hex_val}; }}
</style></head>
<body>
<div class="card">{body}
</div>
</body></html>"""


# ================================================================
#  HTML RENDERER (browser headless)
# ================================================================


def _render_html(browser_path, html_str, output_path, width, height):
    # The browser resolves --screenshot relative to its own CWD, not ours, so a
    # relative output_path fails with "access denied". Always pass an absolute path.
    abs_output = os.path.abspath(output_path)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_str)
        html_path = f.name
    profile_dir = tempfile.mkdtemp(prefix="card_profile_")
    try:
        file_uri = "file:///" + html_path.replace("\\", "/")
        # Modern Chromium/Edge require --headless=new; the bare --headless flag
        # is deprecated and silently produces no screenshot on recent builds.
        # A throwaway --user-data-dir prevents attaching to a running instance
        # (which would cause the launcher to exit before the screenshot is taken).
        base = ["--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                "--no-first-run", "--disable-extensions",
                f"--user-data-dir={profile_dir}",
                "--force-device-scale-factor=1",
                f"--window-size={width},{height}",
                f"--screenshot={abs_output}", file_uri]
        for headless in ("--headless=new", "--headless"):
            if os.path.exists(abs_output):
                try:
                    os.unlink(abs_output)
                except OSError:
                    pass
            result = subprocess.run([browser_path, headless] + base,
                                    capture_output=True, timeout=30)
            # Edge/Chrome may relaunch into a child process and return before the
            # screenshot is flushed to disk. Poll briefly for the file.
            for _ in range(20):
                if os.path.exists(abs_output) and os.path.getsize(abs_output) > 0:
                    return True
                time.sleep(0.25)
        if result.stderr:
            print(f"[WARN] Browser stderr: {result.stderr.decode(errors='ignore').strip()[:200]}")
        return False
    finally:
        os.unlink(html_path)
        shutil.rmtree(profile_dir, ignore_errors=True)


# ================================================================
#  SATORI RENDERER (delegates to Node.js satori-card/generate.js)
# ================================================================

_SATORI_SCRIPT = os.path.normpath(os.path.join(_HERE, "..", "satori-card", "generate.js"))


def _render_satori(url, name, image_path, output_path, theme, fmt_name, subtitle, accent_hex,
                   brand="", platform="", lang="en", features=None, models=""):
    """Invoke the Node.js satori renderer as a subprocess. Returns True on success."""
    if not shutil.which("node"):
        print("[WARN] Node.js not found on PATH; cannot use satori renderer.")
        return False
    if not os.path.exists(_SATORI_SCRIPT):
        print(f"[WARN] Satori script not found: {_SATORI_SCRIPT}")
        return False

    cmd = ["node", _SATORI_SCRIPT,
           "--url", url, "--name", name, "--image", image_path,
           "--theme", theme, "--type", fmt_name, "--output", output_path,
           "--lang", lang]
    if subtitle:
        cmd += ["--subtitle", subtitle]
    if accent_hex:
        cmd += ["--accent", accent_hex]
    if brand:
        cmd += ["--brand", brand]
    if platform:
        cmd += ["--platform", platform]
    if models:
        cmd += ["--models", models]
    # Feature bullets (social layout only); passed through as --f1/--f2/--f3.
    for i, feat in enumerate((features or [])[:3], start=1):
        if feat:
            cmd += [f"--f{i}", feat]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"[WARN] Satori failed: {result.stderr.strip()}")
            return False
        return os.path.exists(output_path)
    except subprocess.TimeoutExpired:
        print("[WARN] Satori renderer timed out.")
        return False


# ================================================================
#  DRAWING PRIMITIVES (Pillow)
# ================================================================


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
    pad = 10
    outer = size + pad * 2
    block = Image.new("RGBA", (outer, outer), (0, 0, 0, 0))
    bd = ImageDraw.Draw(block)
    bd.rounded_rectangle(
        [(0, 0), (outer - 1, outer - 1)],
        radius=theme["qr_radius"], fill=(255, 255, 255, 255),
        outline=theme["divider"] + (255,), width=1,
    )
    block.paste(qr_img, (pad, pad), qr_img)
    return block


# ================================================================
#  PILLOW RENDERER (clean international card-in-canvas design)
# ================================================================


def _wrap_text(draw, text, font, max_w):
    """Wrap text (handles CJK char-by-char and Latin word-by-word)."""
    if draw.textlength(text, font=font) <= max_w:
        return [text]
    lines, cur = [], ""
    has_space = " " in text
    tokens = text.split(" ") if has_space else list(text)
    joiner = " " if has_space else ""
    for tok in tokens:
        trial = (cur + joiner + tok).strip() if cur else tok
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = tok
    if cur:
        lines.append(cur)
    return lines


def _render_pillow(url, name, image_path, output_path, theme, fmt, subtitle, accent_hex,
                   brand="", platform="", lang="en", features=None):
    t = dict(theme)
    if accent_hex:
        t["accent"] = _hex_to_rgb(accent_hex)
    loc = _loc(lang)
    features = [f for f in (features or []) if f][:3]

    cw, ch = fmt["w"], fmt["h"]
    is_landscape = cw > ch

    canvas = Image.new("RGB", (cw, ch), t["canvas_bg"])

    card_x, card_y = CARD_MARGIN, CARD_MARGIN
    card_w = cw - CARD_MARGIN * 2
    card_h = ch - CARD_MARGIN * 2

    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([(0, 0), (card_w - 1, card_h - 1)], radius=CARD_RADIUS, fill=t["card_bg"])

    pad = CARD_PAD

    # Fonts
    f_name = _resolve_font(46 if is_landscape else 56, prefer_bold=True)
    f_sub = _resolve_font(20 if is_landscape else 22)
    f_brand = _resolve_font(18, prefer_bold=True)
    f_platform = _resolve_font(12, prefer_bold=True)
    f_badge = _resolve_font(12, prefer_bold=True)
    f_hint = _resolve_font(12, prefer_bold=True)
    f_url = _resolve_font(16)

    display_url = url.replace("https://", "").replace("http://", "").rstrip("/")

    def _spaced(s, n=2):
        return (" " * (n // 2 + 1)).join(list(s)) if s else s

    # ---- Logo tile ----
    logo_box = 132 if is_landscape else 150
    logo_bg = (255, 255, 255) if not t["dark"] else t["card_bg"]
    logo_tint = 10 if t["dark"] else 8

    ui_img = Image.open(image_path).convert("RGBA")
    inner = logo_box - 52
    ui_img.thumbnail((inner, inner), Image.Resampling.LANCZOS)

    tile = Image.new("RGBA", (logo_box, logo_box), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    tile_fill = tuple(min(255, c + logo_tint) for c in t["card_bg"]) if not t["dark"] else \
        tuple(min(255, c + 14) for c in t["card_bg"])
    td.rounded_rectangle([(0, 0), (logo_box - 1, logo_box - 1)], radius=28,
                         fill=tile_fill, outline=t["divider"] + (255,), width=1)
    lx = (logo_box - ui_img.width) // 2
    ly = (logo_box - ui_img.height) // 2
    tile.paste(ui_img, (lx, ly), ui_img)

    # ---- QR block ----
    qr_size = 132 if is_landscape else 150
    qr_block = _make_qr_block(url, qr_size, t)

    # ================= LANDSCAPE (split row) =================
    if is_landscape:
        # Left: logo centered in left 44%
        left_w = int(card_w * 0.44)
        tile_x = (left_w - logo_box) // 2
        tile_y = (card_h - logo_box) // 2
        card.paste(tile, (tile_x, tile_y), tile)

        # vertical divider
        cd.line([(left_w, pad), (left_w, card_h - pad)], fill=t["divider"], width=1)

        rx = left_w + pad
        rw = card_w - rx - pad
        # Measure content block height to vertically center
        blocks = []
        cur_y = 0
        if brand or platform:
            if brand:
                blocks.append(("brand", brand, 26)); cur_y += 26
            if platform:
                blocks.append(("platform", _spaced(platform, 3), 22)); cur_y += 22
            blocks.append(("gap", "", 20)); cur_y += 20
        blocks.append(("badge", loc["badge"], 34)); cur_y += 34
        name_lines = _wrap_text(cd, name, f_name, rw)
        for nl in name_lines:
            blocks.append(("name", nl, 58)); cur_y += 58
        blocks.append(("gap", "", 6)); cur_y += 6
        sub = subtitle or loc["default_subtitle"]
        for sl in _wrap_text(cd, sub, f_sub, rw):
            blocks.append(("sub", sl, 30)); cur_y += 30
        blocks.append(("rule", "", 30)); cur_y += 30
        footer_h = qr_block.size[1]
        cur_y += 20 + footer_h

        start_y = pad + (card_h - 2 * pad - cur_y) // 2
        y = start_y
        for kind, text, dy in blocks:
            if kind == "brand":
                cd.text((rx, y), text, font=f_brand, fill=t["text_primary"])
            elif kind == "platform":
                cd.text((rx, y), text, font=f_platform, fill=t["text_secondary"])
            elif kind == "badge":
                _draw_badge(cd, rx, y, text, f_badge, t)
            elif kind == "name":
                cd.text((rx, y), text, font=f_name, fill=t["text_primary"])
            elif kind == "sub":
                cd.text((rx, y), text, font=f_sub, fill=t["text_secondary"])
            elif kind == "rule":
                cd.line([(rx, y + 8), (rx + 64, y + 8)], fill=t["divider"], width=1)
            y += dy
        # footer: qr + text
        y += 20
        card.paste(qr_block, (rx, y), qr_block)
        ftx = rx + qr_block.size[0] + 20
        fty = y + (qr_block.size[1] - 42) // 2
        cd.text((ftx, fty), _spaced(loc["scan_hint"], 2), font=f_hint, fill=t["text_secondary"])
        cd.text((ftx, fty + 22), display_url, font=f_url, fill=t["accent"])

    # ================= PORTRAIT / SQUARE (centered) =================
    else:
        cx = card_w // 2
        y = pad
        if brand:
            _center_text(cd, cx, y, brand, f_brand, t["text_primary"]); y += 26
        if platform:
            _center_text(cd, cx, y, _spaced(platform, 3), f_platform, t["text_secondary"]); y += 24
        if brand or platform:
            y += 18

        card.paste(tile, (cx - logo_box // 2, y), tile)
        y += logo_box + 28

        _center_badge(cd, cx, y, loc["badge"], f_badge, t); y += 34

        for nl in _wrap_text(cd, name, f_name, card_w - 2 * pad):
            _center_text(cd, cx, y, nl, f_name, t["text_primary"]); y += 62
        y += 4
        sub = subtitle or loc["default_subtitle"]
        for sl in _wrap_text(cd, sub, f_sub, card_w - 2 * pad):
            _center_text(cd, cx, y, sl, f_sub, t["text_secondary"]); y += 30
        y += 24
        cd.line([(cx - 50, y), (cx + 50, y)], fill=t["divider"], width=1)
        y += 24

        # optional feature bullets (centered)
        if features:
            f_feat = _resolve_font(16)
            dot_r = 3
            for feat in features:
                fw = cd.textlength(feat, font=f_feat)
                total = fw + 14 + dot_r * 2
                start_x = cx - total / 2
                cd.ellipse([(start_x, y + 8), (start_x + dot_r * 2, y + 8 + dot_r * 2)],
                           fill=t["accent"])
                cd.text((start_x + dot_r * 2 + 14, y), feat, font=f_feat, fill=t["text_secondary"])
                y += 28
        fy = card_h - pad - qr_block.size[1]
        total_fw = qr_block.size[0] + 22 + 240
        fx = (card_w - total_fw) // 2
        card.paste(qr_block, (fx, fy), qr_block)
        ftx = fx + qr_block.size[0] + 22
        fty = fy + (qr_block.size[1] - 42) // 2
        cd.text((ftx, fty), _spaced(loc["scan_hint"], 2), font=f_hint, fill=t["text_secondary"])
        cd.text((ftx, fty + 22), display_url, font=f_url, fill=t["accent"])

    # Shadow + paste
    card_with_shadow = _draw_shadow(card, CARD_RADIUS, t["shadow_color"], SHADOW_OFFSET, SHADOW_BLUR)
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(card_with_shadow, (card_x - SHADOW_BLUR, card_y - SHADOW_BLUR), card_with_shadow)

    canvas_rgba.convert("RGB").save(output_path, "PNG", dpi=(300, 300))
    return True


def _draw_badge(draw, x, y, text, font, t):
    tw = draw.textlength(text, font=font)
    draw.rounded_rectangle([(x, y), (x + tw + 28, y + 24)], radius=12,
                           fill=None, outline=t["accent"], width=1)
    draw.text((x + 14, y + 5), text, font=font, fill=t["accent"])


def _center_text(draw, cx, y, text, font, fill):
    tw = draw.textlength(text, font=font)
    draw.text((cx - tw / 2, y), text, font=font, fill=fill)


def _center_badge(draw, cx, y, text, font, t):
    tw = draw.textlength(text, font=font)
    x = cx - (tw + 28) / 2
    draw.rounded_rectangle([(x, y), (x + tw + 28, y + 24)], radius=12,
                           fill=None, outline=t["accent"], width=1)
    draw.text((x + 14, y + 5), text, font=font, fill=t["accent"])


# ================================================================
#  MAIN ORCHESTRATOR
# ================================================================


def generate_card(url, name, image_path, output_path="card.png",
                  theme="tech-innovation", subtitle="", accent_hex=None,
                  fmt_name="landscape", renderer="auto",
                  brand="", platform="", lang="en", features=None, models=""):
    t = THEMES.get(theme, THEMES["tech-innovation"])
    # social-multi shares the social (portrait) canvas and is satori-only.
    is_multi = fmt_name == "social-multi"
    fmt = FORMATS.get("social" if is_multi else fmt_name, FORMATS["landscape"])
    features = [f for f in (features or []) if f]

    if not os.path.exists(image_path):
        print(f"[ERROR] Image not found: {image_path}")
        sys.exit(1)

    # The multi-model template is implemented only in the satori renderer.
    if is_multi and renderer != "satori":
        print("[INFO] format 'social-multi' is satori-only; switching renderer to satori.")
        renderer = "satori"

    # --- satori: delegate to Node.js (no fallback chain) ---
    if renderer == "satori":
        ok = _render_satori(url, name, image_path, output_path, theme, fmt_name,
                            subtitle, accent_hex, brand, platform, lang, features, models)
        if ok:
            print(f"[OK] Card saved -> {output_path}  "
                  f"(theme: {t['name']}, format: {fmt_name}, renderer: satori)")
            return
        if is_multi:
            print("[ERROR] Satori failed and no fallback exists for social-multi.")
            sys.exit(1)
        print("[WARN] Satori renderer failed, falling back to Pillow...")
        _render_pillow(url, name, image_path, output_path, t, fmt,
                       subtitle, accent_hex, brand, platform, lang, features)
        print(f"[OK] Card saved -> {output_path}  "
              f"(theme: {t['name']}, format: {fmt_name}, renderer: pillow)")
        return

    # --- auto / html / pillow ---
    use_html = renderer in ("html", "auto")
    browser = find_browser() if use_html else None

    if browser and renderer in ("html", "auto"):
        logo_b64 = _image_to_b64(image_path)
        qr_b64 = _generate_qr_b64(url)
        html_str = _build_html(url, name, logo_b64, qr_b64, t, fmt,
                               subtitle, accent_hex, brand, platform, lang, features)
        ok = _render_html(browser, html_str, output_path, fmt["w"], fmt["h"])
        if ok:
            print(f"[OK] Card saved -> {output_path}  "
                  f"(theme: {t['name']}, format: {fmt_name}, "
                  f"renderer: html/{os.path.basename(browser)})")
            return
        print("[WARN] HTML render failed, falling back to Pillow...")

    _render_pillow(url, name, image_path, output_path, t, fmt,
                   subtitle, accent_hex, brand, platform, lang, features)
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
  python generate_card.py --url https://example.com --name "Model" --image ui.png --renderer satori
  python generate_card.py --url https://example.com --name "Model" --image ui.png --theme midnight-galaxy --subtitle "Now Available" --accent "#ff6b6b"

Available themes: """ + ", ".join(THEMES.keys()) + """

Available formats: landscape (1200x630), social (800x1280), square (1080x1080)
Available renderers: auto (default), html, pillow, satori
        """,
    )
    parser.add_argument("--url", required=True, help="Target URL (QR code destination)")
    parser.add_argument("--name", required=True, help="Model / product name")
    parser.add_argument("--image", required=True, help="Path to reference UI screenshot / logo")
    parser.add_argument("--output", default="card.png", help="Output image path")
    parser.add_argument("--theme", choices=list(THEMES.keys()), default="tech-innovation")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--accent", default=None, help="Override accent color (hex)")
    parser.add_argument("--brand", default="", help="Optional brand / company name (top of card)")
    parser.add_argument("--platform", default="", help="Optional platform / tagline label")
    parser.add_argument("--lang", choices=list(LOCALES.keys()), default="en",
                        help="Copy language for badge / scan labels (default: en)")
    parser.add_argument("--f1", default="", help="Feature bullet 1 (social/square layout)")
    parser.add_argument("--f2", default="", help="Feature bullet 2 (social/square layout)")
    parser.add_argument("--f3", default="", help="Feature bullet 3 (social/square layout)")
    parser.add_argument("--models", default="",
                        help='Multi-model list for social-multi, e.g. "Sol|desc, Luna|desc, Terra|desc" (satori-only)')
    parser.add_argument("--format", choices=list(FORMATS.keys()) + ["social-multi"], default="landscape",
                        help="Output format (default: landscape). 'social-multi' = multi-model template (satori-only)")
    parser.add_argument("--renderer", choices=["auto", "html", "pillow", "satori"], default="auto",
                        help="Rendering engine (default: auto)")

    args = parser.parse_args()

    generate_card(
        url=args.url, name=args.name, image_path=args.image,
        output_path=args.output, theme=args.theme, subtitle=args.subtitle,
        accent_hex=args.accent, fmt_name=args.format, renderer=args.renderer,
        brand=args.brand, platform=args.platform, lang=args.lang,
        features=[args.f1, args.f2, args.f3], models=args.models,
    )


if __name__ == "__main__":
    main()
