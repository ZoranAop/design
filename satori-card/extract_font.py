#!/usr/bin/env python3
"""
extract_font.py — extract a single TTF from a system .ttc collection.

Satori (opentype.js) cannot read TrueType Collections (.ttc). This helper
pulls one face out of a .ttc and writes it as a standalone .ttf so the
Node.js renderer can load CJK (esp. Japanese kana) fonts. Output is cached
in satori-card/.fonts/ (gitignored) and only regenerated if missing.

Usage:
    python extract_font.py <input.ttc> <output.ttf> [font_number]
"""

import sys

try:
    from fontTools.ttLib import TTFont
except ImportError:
    sys.stderr.write("fontTools not installed. Run: pip install fonttools\n")
    sys.exit(2)


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: python extract_font.py <input.ttc> <output.ttf> [font_number]\n")
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    num = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    try:
        font = TTFont(src, fontNumber=num, lazy=True)
        font.save(dst)
        print(dst)
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"extract failed: {e}\n")
        sys.exit(3)


if __name__ == "__main__":
    main()
