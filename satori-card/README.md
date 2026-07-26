# Satori Card Generator (Node.js)

The **Satori renderer** — an alternative tool-call layer using [`satori`](https://github.com/vercel/satori) (HTML/CSS → SVG) + `@resvg/resvg-js` (SVG → PNG). Produces deterministic, high-fidelity cards without a browser.

Themes are loaded from the shared **[`../themes.json`](../themes.json)** (single source of truth, shared with the Python renderer). All 14 themes and 3 formats are available. See [`../SKILL.md`](../SKILL.md) for the full architecture.

## Install

```bash
npm install
```

Requires [Node.js](https://nodejs.org/) ≥ 18.

## Usage

```bash
# Landscape card (default)
node generate.js --url https://example.com --name "Kimi K3" --image logo.png

# Social portrait card with brand labels + feature bullets
node generate.js --url https://example.com --name "Kimi K3" --image logo.png \
  --type social --subtitle "Next-gen AI model" --brand "Acme" --platform "AI Platform" \
  --f1 "Chat" --f2 "Multimodal" --f3 "Web Search"

# Square format (1:1), Chinese copy
node generate.js --url https://example.com --name "Kimi K3" --image logo.png --type square --lang zh

# Custom accent color
node generate.js --url https://example.com --name "Kimi K3" --image logo.png --theme midnight-galaxy --accent "#ff6b6b"
```

## Options

| Flag         | Default          | Description                          |
|--------------|------------------|--------------------------------------|
| `--url`      | (required)       | Target URL (QR code destination)     |
| `--name`     | (required)       | Model / product name (the hero)      |
| `--image`    | (required)       | Path to logo / screenshot            |
| `--type`     | `landscape`       | `landscape` / `social` / `square`    |
| `--theme`    | `tech-innovation` | Any key from `../themes.json`         |
| `--subtitle` | (locale default) | Subtitle line under the name          |
| `--brand`    | (hidden)         | Optional company / brand name         |
| `--platform` | (hidden)         | Optional platform / tagline label     |
| `--lang`     | `en`             | Label language: `en` or `zh`          |
| `--f1` `--f2` `--f3` | (defaults) | Feature bullets (social layout only) |
| `--accent`   | (theme default)  | Override accent color (hex)          |
| `--output`   | `card.png`        | Output image path                    |

## Layouts

- **landscape** (1200×630) — split layout: logo preview left, name + QR right
- **social** (800×1280) — hero section with logo, NEW badge, feature bullets, QR footer
- **square** (1080×1080) — centered: logo, name, QR + URL row

## Called as a subprocess

This script is also invokable from the Python renderer:

```bash
python ../card_generator/generate_card.py --url https://example.com --name "Kimi K3" --image logo.png --renderer satori
```

## Credits

Design approach informed by Anthropic's [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design), [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines), and [theme-factory](https://github.com/anthropics/skills/tree/main/skills/theme-factory) skills.
