# Design

Design-forward **digital business card** generator. Input a website URL, model name, and a reference UI screenshot — get back a polished, share-ready card with an embedded QR code that opens the URL.

## Architecture: skill → tool call → page generation

```
SKILL.md                         ← skill layer (instructions + design guidance)
  │
  ▼
card_generator/generate_card.py   ← tool call layer (Python, primary)
  │   renderers: auto / html / pillow / satori
  ├── satori-card/generate.js    ← tool call layer (Node.js, Satori renderer)
  │
  ▼
*.png                             ← page generation layer (output card image)
```

All 14 themes are defined once in **[`themes.json`](themes.json)** — the single source of truth loaded by both renderers.

## Quick start

```bash
pip install -r card_generator/requirements.txt
python card_generator/generate_card.py --url https://example.com --name "My Model" --image ui.png
```

## Documentation

| Document | What it covers |
|----------|----------------|
| [**SKILL.md**](SKILL.md) | Skill definition, architecture, how to query other design skills for optimization |
| [card_generator/README.md](card_generator/README.md) | Python renderer: full feature list, themes, formats, renderers, usage |
| [satori-card/README.md](satori-card/README.md) | Node.js Satori renderer: install, usage, feature bullets |

## Renderers at a glance

| Renderer | Path | Description |
|----------|------|-------------|
| `auto` (default) | `card_generator/generate_card.py` | Browser headless → Pillow fallback |
| `html` | `card_generator/generate_card.py` | Force HTML/CSS + browser headless |
| `pillow` | `card_generator/generate_card.py` | Force Pillow/PIL card-in-canvas |
| `satori` | `card_generator/generate_card.py --renderer satori` | Delegates to `satori-card/generate.js` |

## Credits

Design approach informed by Anthropic's [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design), [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines), and [theme-factory](https://github.com/anthropics/skills/tree/main/skills/theme-factory) skills. See `SKILL.md` for how to query them when optimizing the design.
