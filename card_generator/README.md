# Card Generator

**Design-forward shareable card generator.** Input a website URL, model name, and a reference UI screenshot — get back a polished, share-ready card with an embedded QR code.

Built with design philosophy from [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design), color systems from [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines), and theme palettes from [theme-factory](https://github.com/anthropics/skills/tree/main/skills/theme-factory).

## Features

- **Dual rendering engines**: HTML/CSS + browser headless (primary, high fidelity) with automatic Pillow fallback (card-in-canvas design, no browser required)
- **14 design themes**: 4 canvas-design philosophies + 10 theme-factory palettes
- **3 output formats**: landscape (1200×630), social (800×1280), square (1080×1080)
- **QR code** with rounded corners and accent-colored border (scan → opens the URL)
- **Glassmorphism, gradients, grid patterns, glow effects** (HTML renderer)
- **Card-in-canvas layout** with soft drop shadow (Pillow renderer)
- **Typography hierarchy** with automatic font fallback and text wrapping
- **Geometric design elements** unique to each theme
- **Custom accent color** override via `--accent`
- **Browser auto-detection**: Edge → Chrome → Pillow fallback

## Install

```bash
pip install -r requirements.txt
```

For the high-fidelity HTML renderer, ensure a Chromium-based browser is installed (Edge or Chrome). The script auto-detects it. If none is found, it falls back to the Pillow renderer automatically.

## Usage

```bash
# Basic (auto renderer, default theme)
python generate_card.py --url https://example.com --name "My Model" --image ui.png

# Social media format with Tech Innovation theme
python generate_card.py --url https://example.com --name "My Model" --image ui.png --theme tech-innovation --format social

# Force Pillow renderer (no browser needed)
python generate_card.py --url https://example.com --name "My Model" --image ui.png --renderer pillow

# Custom accent color + subtitle
python generate_card.py --url https://example.com --name "My Model" --image ui.png --theme midnight-galaxy --subtitle "Now Available" --accent "#ff6b6b"

# Square format for Instagram
python generate_card.py --url https://example.com --name "My Model" --image ui.png --format square
```

## Themes

### canvas-design philosophies (4)

| Theme    | Mood                                   | Light/Dark |
|----------|----------------------------------------|------------|
| minimal  | Swiss formalism, generous white space  | Light      |
| tech     | Digital precision, data-vis feel       | Dark       |
| organic  | Warm earth tones, rounded forms        | Light      |
| bold     | Monumental geometry, poster energy     | Dark       |

### theme-factory palettes (10)

| Theme              | Mood                              | Light/Dark |
|--------------------|-----------------------------------|------------|
| tech-innovation    | Bold modern tech, AI/ML launches  | Dark       |
| midnight-galaxy    | Dramatic cosmic deep tones        | Dark       |
| ocean-depths       | Calming maritime                  | Dark       |
| sunset-boulevard   | Warm vibrant sunset               | Light      |
| forest-canopy      | Natural grounded earth tones      | Dark       |
| modern-minimalist  | Clean contemporary grayscale      | Light      |
| golden-hour        | Rich warm autumnal                | Dark       |
| arctic-frost       | Cool crisp winter                 | Light      |
| desert-rose        | Soft sophisticated dusty         | Light      |
| botanical-garden   | Fresh organic garden              | Light      |

## Formats

| Format    | Dimensions    | Use case                          |
|-----------|---------------|-----------------------------------|
| landscape | 1200×630      | OG image / link preview           |
| social    | 800×1280      | WeChat Moments / social sharing    |
| square    | 1080×1080     | Instagram feed (1:1)              |

## Renderers

| Renderer | Description                                          |
|----------|------------------------------------------------------|
| auto     | Default — uses browser if available, else Pillow     |
| html     | Force HTML/CSS + browser headless (high fidelity)    |
| pillow   | Force Pillow/PIL card-in-canvas (no browser needed)  |

## Satori Renderer (alternative)

A separate Node.js-based renderer using `@vercel/satori` + `@resvg/resvg-js` is available in [`../satori-card/`](../satori-card/). See its README for usage.

## Credits

Design approach informed by Anthropic's [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design), [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines), and [theme-factory](https://github.com/anthropics/skills/tree/main/skills/theme-factory) skills.
