"""Generate the glowing Legendária key art (hero and banner) as SVG.

Writes into assets/brand/. The text is plain SVG text here; convert it to
paths with Inkscape afterwards (see assets/brand/README.md).
"""

import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent

# Same symbol geometry as generate_brand_svgs.py (1676 px design space).
BARS = "M300 795V880M362 751V925M425 703V972M488 624V1051M551 517V1157M614 624V1051M677 708V947M739 768V882M801 810V840"
LINES = [
    "M738 600L805 715Q860 812 990 836H1375",
    "M700 1125L805 955Q860 860 990 836",
    "M808 590L862 683Q905 757 1000 757H1315",
    "M800 1095L860 995Q905 915 1000 915H1315",
    "M918 645Q945 678 990 678H1212",
    "M918 1030Q945 995 990 995H1212",
]
SYMBOL_BOX = (281, 498, 1394, 1176)  # x0, y0, x1, y1 of the strokes

TAGLINES = {
    "en": "FREE SUBTITLES · CAPCUT STYLE",
    "pt-BR": "LEGENDAS LIVRES · ESTILO CAPCUT",
}

DEFS = """<defs>
    <linearGradient id="lg" gradientUnits="userSpaceOnUse" x1="328" y1="819" x2="510" y2="1276">
      <stop offset="0" stop-color="#FF9A45"/><stop offset="0.4" stop-color="#E9707A"/>
      <stop offset="0.55" stop-color="#C259B8"/><stop offset="0.8" stop-color="#8C3DE0"/>
      <stop offset="1" stop-color="#7028E0"/></linearGradient>
    <linearGradient id="core" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFE3C4"/><stop offset="1" stop-color="#E8C8FF"/></linearGradient>
    <linearGradient id="word" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFF7F2"/><stop offset="1" stop-color="#F3B9A2"/></linearGradient>
    <linearGradient id="streak" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#FFB070" stop-opacity="0"/><stop offset="0.5" stop-color="#FFD9B8" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#C08CFF" stop-opacity="0"/></linearGradient>
    <radialGradient id="bg" cx="0.45" cy="0.45" r="0.75">
      <stop offset="0" stop-color="#1D1E2A"/><stop offset="1" stop-color="#0D1116"/></radialGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="22" result="wide"/>
      <feGaussianBlur in="SourceGraphic" stdDeviation="7" result="near"/>
      <feMerge><feMergeNode in="wide"/><feMergeNode in="near"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>
    <filter id="textglow" x="-20%" y="-50%" width="140%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b"/>
      <feComponentTransfer in="b" result="bf"><feFuncA type="linear" slope="0.45"/></feComponentTransfer>
      <feMerge><feMergeNode in="bf"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>"""


def symbol(x, y, width):
    """Glowing symbol placed so its stroke box starts at (x, y) with the given width."""
    x0, y0, x1, _ = SYMBOL_BOX
    s = width / (x1 - x0)
    lines = "".join(f'<path d="{d}"/>' for d in LINES)
    rnd = random.Random(7)  # deterministic particles
    dots = []
    for _ in range(70):
        px, py = rnd.uniform(230, 860), rnd.uniform(470, 1210)
        r = rnd.choice([2, 3, 3, 4, 5, 7])
        color = rnd.choice(["#FFB36B", "#FF9A45", "#F08AB0", "#B98BFF"])
        dots.append(
            f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{r}" fill="{color}" opacity="{rnd.uniform(0.25, 0.9):.2f}"/>'
        )
    return f"""<g transform="translate({x:.1f} {y:.1f}) scale({s:.4f}) translate({-x0} {-y0})">
    <g filter="url(#soft)">{"".join(dots)}</g>
    <g fill="none" stroke-linecap="round" stroke-linejoin="round">
      <g stroke="#7F78A0" stroke-opacity="0.34" stroke-width="40" transform="translate(16 18)">{lines}</g>
      <g stroke="url(#lg)" stroke-width="37" filter="url(#glow)"><path d="{BARS}"/>{lines}</g>
      <g stroke="url(#core)" stroke-width="8"><path d="{BARS}" stroke-opacity="0.6"/><g stroke-opacity="0.28">{lines}</g></g>
    </g>
    <rect x="150" y="833" width="760" height="5" rx="2.5" fill="url(#streak)" filter="url(#soft)"/>
  </g>"""


def background(w, h):
    """Dark radial background with faint diagonal shapes and bands."""
    return f"""<rect width="{w}" height="{h}" fill="url(#bg)"/>
  <path d="M{w * 0.55:.0f} 0L{w} 0L{w} {h * 0.45:.0f}Z" fill="#FFFFFF" opacity="0.025"/>
  <path d="M0 {h * 0.78:.0f}L{w * 0.4:.0f} {h}L0 {h}Z" fill="#FFFFFF" opacity="0.02"/>
  <g fill="#FFFFFF" opacity="0.018">
    <rect x="{w * 0.62:.0f}" y="{h * 0.30:.0f}" width="{w * 0.38:.0f}" height="{h * 0.035:.0f}"/>
    <rect x="{w * 0.70:.0f}" y="{h * 0.40:.0f}" width="{w * 0.30:.0f}" height="{h * 0.035:.0f}"/>
    <rect x="{w * 0.66:.0f}" y="{h * 0.62:.0f}" width="{w * 0.34:.0f}" height="{h * 0.035:.0f}"/>
  </g>"""


def text(x, y, size, anchor, tagline, tag_size, tag_dy):
    """Montserrat wordmark with glow plus the spaced tagline."""
    return f"""<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Montserrat" font-weight="400"
        font-size="{size}" fill="url(#word)" filter="url(#textglow)">Legendária</text>
  <text x="{x}" y="{y + tag_dy}" text-anchor="{anchor}" font-family="Montserrat" font-weight="500"
        font-size="{tag_size}" letter-spacing="{tag_size * 0.16:.1f}" fill="#E9B79C">{tagline}</text>"""


def svg(w, h, body):
    """Wrap a body in <svg> with defs, title and label."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="Legendária">\n  <title>Legendária</title>\n  {DEFS}\n  {body}\n</svg>\n'
    )


for lang, tagline in TAGLINES.items():
    # Square key art, same layout as the reference.
    hero = (
        background(1024, 1024)
        + symbol(195, 300, 640)
        + text(512, 835, 104, "middle", tagline, 29, 72)
    )
    (OUT / f"hero-{lang}.svg").write_text(svg(1024, 1024, hero), encoding="utf-8")
    # Wide banner for the README and the social preview (1280x640).
    banner = (
        background(1280, 640) + symbol(80, 205, 410) + text(555, 352, 110, "start", tagline, 26, 66)
    )
    (OUT / f"banner-{lang}.svg").write_text(svg(1280, 640, banner), encoding="utf-8")
