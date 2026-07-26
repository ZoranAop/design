# Card Generator (Python)

Design-forward shareable card generator — the **primary tool-call layer** of this repo. Input a website URL, model name, and a reference UI screenshot — get back a polished, share-ready card with an embedded QR code.

Themes are loaded from the shared **[`../themes.json`](../themes.json)** (single source of truth, shared with the Node.js Satori renderer). See [`../SKILL.md`](../SKILL.md) for the full architecture and how to query other design skills.

## Features

- **4 renderers**: `auto` (browser → Pillow fallback), `html` (force browser), `pillow` (force pure-Python), `satori` (delegates to Node.js)
- **16 design themes**: 4 canvas-design philosophies + 10 theme-factory palettes + X/Twitter dark & light Western-editorial social styles (from `themes.json`)
- **3 output formats**: landscape (1200×630), social (800×1280), square (1080×1080)
- **Clean international layout**: one hero name, generous whitespace, single accent rule + outlined badge, subtle shadow — no clutter
- **Configurable branding**: optional `--brand` and `--platform` labels (hidden when omitted, so cards stay generic and reusable)
- **Localized copy**: `--lang en|zh|zh-Hant|ja` drives all labels (badge / scan hint) from one unified table — never mixes languages
- **QR code** with rounded corners (scan → opens the URL)
- **Custom accent color** override via `--accent`
- **Browser auto-detection**: Edge → Chrome → Pillow fallback (uses `--headless=new` + absolute output path)

## Install

```bash
pip install -r requirements.txt
```

For the high-fidelity HTML renderer, ensure a Chromium-based browser is installed (Edge or Chrome). The script auto-detects it. If none is found, it falls back to the Pillow renderer automatically.

For the `satori` renderer, ensure [Node.js](https://nodejs.org/) is installed and run `npm install` in `../satori-card/` once.

## Usage

```bash
# Basic (auto renderer, default theme)
python generate_card.py --url https://example.com --name "My Model" --image ui.png

# Social media format with Tech Innovation theme + brand labels
python generate_card.py --url https://example.com --name "My Model" --image ui.png \
  --theme tech-innovation --format social --brand "Acme" --platform "AI Platform"

# Satori renderer (delegates to Node.js), square format, Chinese copy
python generate_card.py --url https://example.com --name "My Model" --image ui.png \
  --renderer satori --format square --lang zh

# Force Pillow renderer (no browser needed)
python generate_card.py --url https://example.com --name "My Model" --image ui.png --renderer pillow

# Custom accent color + subtitle
python generate_card.py --url https://example.com --name "My Model" --image ui.png \
  --theme midnight-galaxy --subtitle "Now Available" --accent "#ff6b6b"

# Square format for Instagram
python generate_card.py --url https://example.com --name "My Model" --image ui.png --format square
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--url` | (required) | Target URL (QR destination) |
| `--name` | (required) | Model / product / series name (the hero) |
| `--image` | (required) | Logo / reference screenshot |
| `--theme` | `tech-innovation` | Any key from `../themes.json` |
| `--format` | `landscape` | `landscape` / `social` / `social-multi` / `square` |
| `--subtitle` | (locale default) | One-line descriptor under the name |
| `--brand` | (hidden) | Optional company / brand name |
| `--platform` | (hidden) | Optional platform / tagline label |
| `--f1` `--f2` `--f3` | (hidden) | Feature bullets (social / square layouts) |
| `--models` | (none) | Multi-model list for `social-multi`: `"Name\|desc, …"` (satori-only) |
| `--lang` | `en` | Label language: `en` / `zh` / `zh-Hant` / `ja` |
| `--accent` | (theme default) | Override accent color (hex) |
| `--renderer` | `auto` | `auto` / `html` / `pillow` / `satori` |
| `--output` | `card.png` | Output image path |

## Renderers

| Renderer | Description                                          |
|----------|------------------------------------------------------|
| auto     | Default — uses browser if available, else Pillow     |
| html     | Force HTML/CSS + browser headless (high fidelity)    |
| pillow   | Force Pillow/PIL card-in-canvas (no browser needed)  |
| satori   | Delegate to Node.js `../satori-card/generate.js`     |

## Themes & formats

See [`../themes.json`](../themes.json) for the full, authoritative list of 16 themes and 3 formats. Both are defined there once and consumed by this script and the Satori renderer.

## Credits

Design approach informed by Anthropic's [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design), [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines), and [theme-factory](https://github.com/anthropics/skills/tree/main/skills/theme-factory) skills.
