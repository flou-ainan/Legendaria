# Legendária brand kit

The symbol shows **a sound wave flowing into lines of text**: speech becoming subtitles, read left to right. The concept was explored with Google Gemini (references in `source/`) and redrawn as a clean vector for Legendária.

## Files

| File | Use |
|---|---|
| `legendaria-symbol.svg` | Main symbol, full color, transparent background |
| `legendaria-symbol-mono.svg` | Single color (`currentColor`): watermarks, print, the Blender UI |
| `legendaria-icon.svg` | App icon: full symbol on a dark rounded square (≥ 128 px) |
| `legendaria-icon-small.svg` | Simplified icon for 16–64 px (favicon, tabs, small UI) |
| `lockup-<font>-light.svg` / `-dark.svg` | Symbol + "Legendária" wordmark, for light / dark backgrounds |
| `social-<font>.svg` | 1280×640 social preview (GitHub, link cards) |
| `favicon.ico` | 16/32/48 px favicon |
| `png/` | Pre-rendered PNGs of the icons, the symbol and the social preview |
| `source/` | Gemini reference images and `generate_brand_svgs.py` |

The lockup and social SVGs have their text converted to paths, so they render the same without the font installed.

## Colors

| Token | Hex | Where |
|---|---|---|
| Orange | `#FF8A3D` | gradient start (top / left) |
| Coral | `#D96771` | gradient 40% |
| Magenta | `#B5509F` | gradient 55% |
| Violet | `#7E27CC` | gradient 80% |
| Purple | `#6418CB` | gradient end (bottom / right) |
| Ink | `#111822` | dark background |
| Text on light | `#151A23` | wordmark on light backgrounds |
| Text on dark | `#F4F1FA` | wordmark on dark backgrounds |

## Typography

The wordmark has two candidates, both under the SIL Open Font License: **Montserrat SemiBold** and **Nunito ExtraBold**. Nunito's rounded terminals match the symbol's round caps.

## Rules

- Keep clear space around the symbol of at least the height of its shortest bar.
- Do not add glow, shadows or outlines; do not change the gradient direction; do not stretch.
- Below 64 px, use `legendaria-icon-small.svg`.
- Do not use "Blender" in any brand material (Blender Foundation trademark).

## Regenerating

`source/generate_brand_svgs.py` draws the symbol, the icons and the (text-based) lockups. Convert the text to paths with Inkscape afterwards:

```bash
inkscape lockup-nunito-dark.svg --export-text-to-path --export-plain-svg --export-type=svg --export-filename=lockup-nunito-dark.svg
```
