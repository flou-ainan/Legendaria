# Legendária brand kit

The symbol shows **a sound wave flowing into lines of text**: speech becoming subtitles, read left to right. The concept was explored with Google Gemini (references in `source/`) and redrawn as clean vectors for Legendária.

The brand has two finishes of the same symbol:

- **Glow (key art):** for anything large, such as the README, the website, the social preview and video thumbnails.
- **Flat:** icons, favicon, UI, print, and anything small.

## Files

| File | Use |
|---|---|
| `banner-en.svg` / `banner-pt-BR.svg` | **Main key art**, 1280×640: glowing symbol + wordmark + tagline. Top of the READMEs |
| `cover-en.svg` / `cover-pt-BR.svg` | **Social preview**, 1280×640: key art plus what the project does and the repo link. PNGs in `png/social-preview-<lang>.png`; upload the English one under GitHub → Settings → Social preview |
| `hero-en.svg` / `hero-pt-BR.svg` | Square key art, 1024×1024: website hero, video thumbnails, posts |
| `legendaria-symbol.svg` | Flat symbol, full color, transparent background |
| `legendaria-symbol-mono.svg` | Single color (`currentColor`): watermarks, print, the Blender UI |
| `legendaria-icon.svg` | App icon: flat symbol on a dark rounded square (≥ 128 px) |
| `legendaria-icon-small.svg` | Simplified icon for 16–64 px (favicon, tabs, small UI) |
| `legendaria-lockup-light.svg` / `-dark.svg` | Flat symbol + wordmark, for light / dark backgrounds |
| `favicon.ico` | 16/32/48 px favicon |
| `png/` | Pre-rendered PNGs: icons, symbol, lockup, hero at 2048 px, `social-preview-<lang>.png` |
| `source/` | Gemini reference images and the two generator scripts |

Every SVG here has its text converted to paths, so it renders the same without the font installed. The glow is made with SVG filters, so it scales to any size.

## Taglines

| Language | Tagline |
|---|---|
| en | FREE SUBTITLES · CAPCUT STYLE |
| pt-BR | LEGENDAS LIVRES · ESTILO CAPCUT |

To add a language, add entries to `TAGLINES` and `PITCH` in `source/generate_hero.py` and regenerate.

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
| Peach | `#E9B79C` | tagline on the key art |

The glow finish uses a slightly brighter variant of the gradient (see `generate_hero.py`).

## Typography

**Montserrat** (SIL Open Font License): Regular for the key-art wordmark, Medium for the flat lockups and the taglines.

## Rules

- Keep clear space around the symbol of at least the height of its shortest bar.
- Do not add glow to the flat finish below 128 px. Do not change the gradient direction; do not stretch.
- Below 64 px, use `legendaria-icon-small.svg`.
- Do not use "Blender" in any brand material (Blender Foundation trademark).

## Regenerating

You need Python 3, Inkscape and the Montserrat font:

```bash
python3 assets/brand/source/generate_brand_svgs.py   # flat symbol, icons, lockups
python3 assets/brand/source/generate_hero.py         # glowing hero + banner, per language
# then convert the text to paths, for each lockup/hero/banner file:
inkscape FILE.svg --export-text-to-path --export-plain-svg --export-type=svg --export-filename=FILE.svg
```
