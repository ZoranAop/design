# Design

Design-forward shareable card generator. Input a website URL, model name, and a reference UI screenshot — get back a polished, print-ready card with an embedded QR code.

Built with design philosophy from [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design) and color-system principles from [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines).

## Quick Start

```bash
pip install -r card_generator/requirements.txt
python card_generator/generate_card.py --url https://example.com --name "My Model" --image ui.png
```

See [card_generator/README.md](card_generator/README.md) for full documentation.

## Features

- **4 design themes** — Minimal, Tech, Organic, Bold — each with distinct color palette, typography rhythm, and geometric accents
- **QR code** with rounded corners and theme-colored border (scan → opens the URL)
- **Rounded UI screenshot** with soft drop shadow
- **Typography hierarchy** with automatic font fallback
- **Geometric design elements** unique to each theme
- Custom accent color override via `--accent`

## Themes

| Theme    | Mood                                   |
|----------|----------------------------------------|
| minimal  | Swiss formalism, generous white space  |
| tech     | Digital precision, data-vis aesthetic  |
| organic  | Warm earth tones, rounded forms        |
| bold     | Monumental geometry, poster energy     |

## Credits

Design approach informed by Anthropic's [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design) and [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines) skills.
