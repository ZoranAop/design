---
name: digital-business-card
description: Generate a design-forward digital business card with an embedded QR code from a URL. Use when the user wants to create a shareable card image that links to a website, model page, or product page. Produces landscape / social / square PNG cards with 14 design themes. Can query canvas-design, brand-guidelines, and theme-factory skills for design optimization.
---

# Digital Business Card Skill

## What this skill does

Parses a **URL** → generates a **QR code** → composes it onto a polished **digital business card** → outputs a **PNG image** ready for sharing.

The card surfaces a model/product name, an optional subtitle, a reference logo/screenshot, and a scannable QR code that opens the target URL. Three output formats cover the common share surfaces:

| Format    | Dimensions    | Use case                          |
|-----------|---------------|-----------------------------------|
| landscape | 1200×630      | OG image / link preview           |
| social    | 800×1280      | WeChat Moments / social sharing   |
| square    | 1080×1080     | Instagram feed (1:1)              |

## Architecture: skill → tool call → page generation

```
SKILL.md  ──(this file, the "skill" layer: instructions + design guidance)
    │
    ▼  instructs the agent to call
card_generator/generate_card.py   ──(Python, the primary "tool call" layer)
    │   renderers: auto / html / pillow / satori
    │
    ├── satori-card/generate.js  ──(Node.js, invoked as subprocess by --renderer satori)
    │
    ▼  produces
*.png  ──(the "page generation" layer: the final shareable card image)
```

- **Skill layer** = `SKILL.md` (this file). Describes intent, design principles, and how to invoke the tools. References other skills for design optimization.
- **Tool call layer** = `card_generator/generate_card.py` (primary) and `satori-card/generate.js` (Satori renderer). Both load themes from the shared `themes.json` (single source of truth).
- **Page generation layer** = the output PNG image, rendered via HTML/CSS + browser headless, Pillow, or Satori+Resvg.

## Shared theme source

All 14 themes live in **`themes.json`** at the repo root — the single source of truth loaded by both the Python and Node.js renderers. Do not duplicate theme values in code. To add or tweak a theme, edit `themes.json` once and both renderers pick it up.

- 4 **canvas-design** philosophies: `minimal`, `tech`, `organic`, `bold`
- 10 **theme-factory** palettes: `tech-innovation`, `midnight-galaxy`, `ocean-depths`, `sunset-boulevard`, `forest-canopy`, `modern-minimalist`, `golden-hour`, `arctic-frost`, `desert-rose`, `botanical-garden`

## How to invoke (tool call)

### Python (primary, all renderers)

```bash
pip install -r card_generator/requirements.txt

# auto renderer (browser → Pillow fallback), default theme
python card_generator/generate_card.py --url https://example.com --name "My Model" --image ui.png

# social format + theme-factory palette
python card_generator/generate_card.py --url https://example.com --name "My Model" --image ui.png --theme tech-innovation --format social

# Satori renderer (delegates to Node.js), square format
python card_generator/generate_card.py --url https://example.com --name "My Model" --image ui.png --renderer satori --format square

# custom accent color + subtitle
python card_generator/generate_card.py --url https://example.com --name "My Model" --image ui.png --theme midnight-galaxy --subtitle "Now Available" --accent "#ff6b6b"
```

### Node.js (Satori directly)

```bash
cd satori-card && npm install
node generate.js --url https://example.com --name "Kimi K3" --image logo.png --type social --subtitle "新一代 AI 模型" --f1 "AI 对话" --f2 "多模态"
```

## Renderers

| Renderer | Engine                                  | When to use                                   |
|----------|-----------------------------------------|-----------------------------------------------|
| auto     | browser headless → Pillow fallback      | Default; best available fidelity              |
| html     | HTML/CSS + browser headless (Chromium)  | High fidelity: glassmorphism, gradients, glow |
| pillow   | Pillow/PIL card-in-canvas               | No browser; pure-Python environments          |
| satori   | @vercel/satori + @resvg/resvg-js (Node) | Deterministic SVG pipeline; great for CI      |

## Design optimization: querying other skills

This skill is design-informed by Anthropic's design skills. When the user asks to **improve the visual quality, adjust the color system, or craft a new theme**, consult these sibling skills before editing `themes.json`:

- **canvas-design** — `https://github.com/anthropics/skills/tree/main/skills/canvas-design`
  Layout philosophy, spacing rhythm, visual hierarchy. Use when restructuring card composition or adding a new layout.
- **brand-guidelines** — `https://github.com/anthropics/skills/tree/main/skills/brand-guidelines`
  Color systems, contrast, accessibility. Use when defining a new palette or fixing contrast ratios.
- **theme-factory** — `https://github.com/anthropics/skills/tree/main/skills/theme-factory`
  Ready-made theme palettes. Use as the source when adding new theme-factory entries to `themes.json`.

### Adding a new theme

1. Consult **theme-factory** (or **brand-guidelines** for custom palettes) to pick colors with proper contrast.
2. Append an entry to `themes.json` → `themes` with: `name`, `category`, `mood`, `dark`, `colors` (7 hex keys), `shadow` (rgba), `ui_radius`, `qr_radius`.
3. Both renderers automatically pick it up — no code changes needed.
4. The new theme key becomes a valid `--theme` choice in both CLIs.

## Output

The generated card is a PNG (300 DPI for Pillow). Default output path is `card.png` in the working directory; override with `--output`.

The QR code encodes the exact `--url` value. Scanning it opens that URL in the browser.
