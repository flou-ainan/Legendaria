"""Generate the Legendária brand SVGs."""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent  # writes into assets/brand/

GRAD = """<linearGradient id="lg" gradientUnits="userSpaceOnUse" x1="328" y1="819" x2="510" y2="1276">
      <stop offset="0" stop-color="#FF8A3D"/><stop offset="0.4" stop-color="#D96771"/>
      <stop offset="0.55" stop-color="#B5509F"/><stop offset="0.8" stop-color="#7E27CC"/>
      <stop offset="1" stop-color="#6418CB"/></linearGradient>"""

PATHS = """<path d="M300 795V880M362 751V925M425 703V972M488 624V1051M551 517V1157M614 624V1051M677 708V947M739 768V882M801 810V840"/>
    <path d="M738 600L805 715Q860 812 990 836H1375"/>
    <path d="M700 1125L805 955Q860 860 990 836"/>
    <path d="M808 590L862 683Q905 757 1000 757H1315"/>
    <path d="M800 1095L860 995Q905 915 1000 915H1315"/>
    <path d="M918 645Q945 678 990 678H1212"/>
    <path d="M918 1030Q945 995 990 995H1212"/>"""

SYMBOL_VB = "262 480 1152 716"

def group(stroke, width=37):
    return f'<g fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">\n    {PATHS}\n  </g>'

def write(name, body, vb, w=None, h=None, title="Legendária"):
    size = f' width="{w}" height="{h}"' if w else ""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"{size} role="img" aria-label="{title}">\n  <title>{title}</title>\n  {body}\n</svg>\n'
    (OUT / name).write_text(svg, encoding="utf-8")

# 1. Symbol, full color, transparent background.
write("legendaria-symbol.svg", f"<defs>{GRAD}</defs>\n  {group('url(#lg)')}", SYMBOL_VB)
# 2. Symbol, single color (inherits currentColor; black by default).
write("legendaria-symbol-mono.svg", group("currentColor"), SYMBOL_VB)
# 3. App icon: full symbol on a dark rounded square.
write("legendaria-icon.svg",
      f'<defs>{GRAD}</defs>\n  <rect x="138" y="138" width="1400" height="1400" rx="300" fill="#111822"/>\n  {group("url(#lg)", 40)}',
      "138 138 1400 1400")

# 4. Small icon (16–64 px): fewer, thicker strokes, same idea.
SMALL = """<path d="M76 216V296M140 160V352M204 100V412M268 170V342"/>
    <path d="M326 140Q356 236 412 256H448"/>
    <path d="M326 372Q356 276 412 256"/>
    <path d="M410 166H448M410 346H448"/>"""
SMALL_GRAD = """<linearGradient id="sg" gradientUnits="userSpaceOnUse" x1="200" y1="110" x2="330" y2="420">
      <stop offset="0" stop-color="#FF8A3D"/><stop offset="0.45" stop-color="#D0607E"/>
      <stop offset="1" stop-color="#6418CB"/></linearGradient>"""
write("legendaria-icon-small.svg",
      f'<defs>{SMALL_GRAD}</defs>\n  <rect width="512" height="512" rx="112" fill="#111822"/>\n  <g fill="none" stroke="url(#sg)" stroke-width="38" stroke-linecap="round" stroke-linejoin="round">\n    {SMALL}\n  </g>',
      "0 0 512 512")

# 5. Lockups (symbol + wordmark); text converted to paths later by Inkscape.
def lockup(name, font, weight, fill, bg=None):
    rect = f'<rect x="200" y="420" width="4400" height="840" fill="{bg}"/>\n  ' if bg else ""
    body = (f"<defs>{GRAD}</defs>\n  {rect}{group('url(#lg)')}\n"
            f'  <text x="1500" y="1010" font-family="{font}" font-weight="{weight}" font-size="440" fill="{fill}" letter-spacing="-6">Legendária</text>')
    write(name, body, "200 420 4400 840")

for tag, font, weight in [("montserrat", "Montserrat", 600), ("nunito", "Nunito", 800)]:
    lockup(f"lockup-{tag}-light.svg", font, weight, "#151A23", "#FFFFFF")
    lockup(f"lockup-{tag}-dark.svg", font, weight, "#F4F1FA", "#111822")
print(sorted(p.name for p in OUT.iterdir()))
