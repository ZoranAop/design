# Design

Design-forward shareable card generator. Input a website URL, model name, and a reference UI screenshot — get back a polished, share-ready card with an embedded QR code.

Built with design philosophy from [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design), color systems from [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines), and theme palettes from [theme-factory](https://github.com/anthropics/skills/tree/main/skills/theme-factory).

## Quick Start

```bash
pip install -r card_generator/requirements.txt
python card_generator/generate_card.py --url https://example.com --name "My Model" --image ui.png
```

See [card_generator/README.md](card_generator/README.md) for full documentation.

## Features

- **Dual rendering engines** — HTML/CSS + browser headless (primary) with automatic Pillow fallback (card-in-canvas design)
- **14 design themes** — 4 canvas-design philosophies + 10 theme-factory palettes
- **3 output formats** — landscape (1200×630), social (800×1280), square (1080×1080)
- **QR code** with rounded corners and theme-colored border (scan → opens the URL)
- **Glassmorphism, gradients, grid patterns, glow effects** (HTML renderer)
- **Card-in-canvas layout** with soft drop shadow (Pillow renderer)
- **Typography hierarchy** with automatic font fallback and text wrapping
- **Geometric design elements** unique to each theme
- Custom accent color override via `--accent`
- Browser auto-detection (Edge → Chrome → Pillow fallback)

## Renderers

| Renderer | Path | Description |
|----------|------|-------------|
| `auto` (default) | `card_generator/generate_card.py` | Browser headless → Pillow fallback |
| `html` | `card_generator/generate_card.py` | Force HTML/CSS + browser headless |
| `pillow` | `card_generator/generate_card.py` | Force Pillow/PIL card-in-canvas |
| `satori` | `satori-card/generate.js` | Node.js Satori + Resvg (separate) |

## Themes

### canvas-design philosophies

| Theme    | Mood                                   |
|----------|----------------------------------------|
| minimal  | Swiss formalism, generous white space  |
| tech     | Digital precision, data-vis aesthetic  |
| organic  | Warm earth tones, rounded forms        |
| bold     | Monumental geometry, poster energy     |

### theme-factory palettes

| Theme              | Mood                              |
|--------------------|-----------------------------------|
| tech-innovation    | Bold modern tech, AI/ML launches  |
| midnight-galaxy    | Dramatic cosmic deep tones        |
| ocean-depths       | Calming maritime                  |
| sunset-boulevard   | Warm vibrant sunset               |
| forest-canopy      | Natural grounded earth tones      |
| modern-minimalist  | Clean contemporary grayscale      |
| golden-hour        | Rich warm autumnal                |
| arctic-frost       | Cool crisp winter                 |
| desert-rose        | Soft sophisticated dusty         |
| botanical-garden   | Fresh organic garden              |

## Credits

Design approach informed by Anthropic's [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design), [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines), and [theme-factory](https://github.com/anthropics/skills/tree/main/skills/theme-factory) skills.
