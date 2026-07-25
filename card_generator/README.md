# Card Generator

**Design-forward shareable card generator.** Input a website URL, model name, and a reference UI screenshot — get back a polished, print-ready card with an embedded QR code.

Built with design philosophy from [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design) and color-system principles from [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines).

## Features

- **4 built-in design themes**: Minimal, Tech, Organic, Bold — each with its own color palette, typography rhythm, and geometric accents
- **QR code** with rounded corners and accent-colored border
- **Rounded UI screenshot** with soft drop shadow
- **Typography hierarchy**: heading / body / caption levels with automatic font fallback
- **Geometric design elements** unique to each theme
- **Custom accent color** override via `--accent`

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Basic
python generate_card.py --url https://example.com --name "My Model" --image ui.png

# With theme
python generate_card.py --url https://example.com --name "My Model" --image ui.png --theme tech

# With subtitle + custom accent
python generate_card.py --url https://example.com --name "My Model" --image ui.png --theme organic --subtitle "A next-gen assistant" --accent "#ff6b6b"

# Custom output path
python generate_card.py --url https://example.com --name "My Model" --image ui.png --output dist/share.png
```

## Themes

| Theme    | Mood                                   | Light/Dark |
|----------|----------------------------------------|------------|
| minimal  | Swiss formalism, generous white space  | Light      |
| tech     | Digital precision, data-vis feel       | Dark       |
| organic  | Warm earth tones, rounded forms        | Light      |
| bold     | Monumental geometry, poster energy     | Dark       |

## Output

Generates a 1000×620 PNG at 300 DPI with:
- Top-left: rounded UI screenshot with shadow
- Right: model name, subtitle, theme badge, URL
- Bottom-right: QR code (scan → opens the URL)

## Credits

Design approach informed by Anthropic's [canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design) and [brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines) skills.
