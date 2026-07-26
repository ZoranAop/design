# Satori Card Generator (Node.js)

The **Satori renderer** — an alternative tool-call layer using [`satori`](https://github.com/vercel/satori) (HTML/CSS → SVG) + `@resvg/resvg-js` (SVG → PNG). Produces deterministic, high-fidelity cards without a browser.

Themes are loaded from the shared **[`../themes.json`](../themes.json)** (single source of truth, shared with the Python renderer). All 14 themes and 3 formats are available. See [`../SKILL.md`](../SKILL.md) for the full architecture.

## Install

```bash
npm install
```

Requires [Node.js](https://nodejs.org/) ≥ 18.

### Fonts (CJK)

Satori (opentype.js) cannot read `.ttc` collections, and Windows ships its
Japanese / Traditional-Chinese fonts only as `.ttc`. For `--lang ja` and
`--lang zh-Hant`, this renderer extracts a single `.ttf` from the system
collection **once** (via `extract_font.py`) and caches it in `.fonts/`
(gitignored). This requires **Python + fontTools**:

```bash
pip install fonttools
```

`--lang en` and `--lang zh` work out of the box (Segoe UI + SimHei). If Python
or the source fonts are missing, other languages still render but Japanese kana
may fall back to tofu boxes.

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

# Multi-model launch card (reusable template): one series + a list of models
node generate.js --url https://platform.ope.ai/market --name "GPT-5.6" --image logo.png \
  --type social-multi --theme light-editorial --platform "AI Platform" \
  --subtitle "Three specialized models. One family." \
  --models "GPT-5.6-Sol|Balanced flagship for everyday reasoning, Luna|Fast & lightweight for real-time apps, Terra|Deep reasoning with long context"

# Custom accent color
node generate.js --url https://example.com --name "Kimi K3" --image logo.png --theme midnight-galaxy --accent "#ff6b6b"

# Localized copy: Japanese / Traditional Chinese (needs fontTools; see Fonts above)
node generate.js --url https://platform.ope.ai/market --name "Kimi K3" --image logo.png \
  --type social --theme x-dark --lang ja --subtitle "より賢く、より速い推論"
node generate.js --url https://platform.ope.ai/market --name "GPT-5.6" --image logo.png \
  --type social-multi --theme light-editorial --lang zh-Hant \
  --models "Sol|日常推理的均衡旗艦, Luna|即時應用的輕量高速版, Terra|長上下文深度推理"
```

## Options

| Flag         | Default          | Description                          |
|--------------|------------------|--------------------------------------|
| `--url`      | (required)       | Target URL (QR code destination)     |
| `--name`     | (required)       | Model / product / **series** name (the hero) |
| `--image`    | (required)       | Path to logo / screenshot            |
| `--type`     | `landscape`       | `landscape` / `social` / `social-multi` / `square` |
| `--theme`    | `tech-innovation` | Any key from `../themes.json`         |
| `--subtitle` | (locale default) | Subtitle line under the name          |
| `--brand`    | (hidden)         | Optional company / brand name         |
| `--platform` | (hidden)         | Optional platform / tagline label     |
| `--lang`     | `en`             | Label language: `en` / `zh` / `zh-Hant` / `ja` |
| `--f1` `--f2` `--f3` | (defaults) | Feature bullets (social layout only) |
| `--models`   | (none)           | `social-multi` list: `"Name\|desc, Name\|desc, ..."` |
| `--accent`   | (theme default)  | Override accent color (hex)          |
| `--output`   | `card.png`        | Output image path                    |

## Layouts

- **landscape** (1200×630) — split layout: logo preview left, name + QR right
- **social** (800×1280) — top wordmark, large hero name, feature bullets, QR footer
- **social-multi** (800×1280) — **reusable multi-model template**: top wordmark, series
  hero, a vertical list of model row-cards (index chip + name + one-line description), QR footer.
  Best paired with `--theme x-dark` (X style) or `--theme light-editorial` (Western editorial).
- **square** (1080×1080) — centered: logo, name, QR + URL row

## Called as a subprocess

This script is also invokable from the Python renderer:

```bash
python ../card_generator/generate_card.py --url https://example.com --name "Kimi K3" --image logo.png --renderer satori
```

## Credits

Design approach informed by Anthropic's [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design), [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines), and [theme-factory](https://github.com/anthropics/skills/tree/main/skills/theme-factory) skills.
