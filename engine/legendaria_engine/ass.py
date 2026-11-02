"""Styled subtitles: cues → Advanced SubStation Alpha (`.ass`), rendered by libass (ADR-012).

The look of a style lives in its `ass` block in the config (font, size at 1080 px, colors as
RGBA floats, outline, shadow, box, position, uppercase, animation). Each cue becomes one
`Dialogue` event positioned with `\\an5\\pos`, so an animation only affects that cue.
"""

from __future__ import annotations

from typing import Any

from legendaria_engine import fonts
from legendaria_engine.cues import CueList, wrap_lines

DEFAULT_SIZE = (1920, 1080)
BASE_HEIGHT = 1080  # sizes in the config are for a 1080 px video (the shorter side)

DEFAULT_LOOK: dict[str, Any] = {
    "font": "Arial",
    "font_size": 64,
    "bold": True,
    "color": [1.0, 1.0, 1.0, 1.0],
    "outline_color": [0.0, 0.0, 0.0, 1.0],
    "outline": 4,
    "shadow": 2,
    "shadow_color": [0.0, 0.0, 0.0, 0.6],
    "box": False,
    "box_color": [0.0, 0.0, 0.0, 0.55],
    "box_padding": [
        0.35,
        0.06,
    ],  # extra width and height on each side, as a fraction of the font size
    "box_radius": 0.25,  # corner roundness, as a fraction of the font size
    "position": [0.5, 0.15],
    "width": 0.9,
    "uppercase": False,
    "animation": {"type": "none"},
}


def with_look(base: dict[str, Any] | None, override: dict[str, Any] | None) -> dict[str, Any]:
    """The style's look with the project's overrides: `font`, `size` (multiplies font, outline and shadow), `y`, colours, `outline`, `shadow` (+ colour, opacity, on/off), `box` (+ colour, opacity, padding, radius) and `uppercase`."""
    look = {**DEFAULT_LOOK, **(base or {})}
    override = override or {}
    if "font" in override:
        look["font"] = override["font"]
    for key in ("outline", "shadow"):
        if key in override:
            look[key] = override[key]
    if "size" in override:
        for key in ("font_size", "outline", "shadow"):
            look[key] = look[key] * override["size"]
    if "y" in override:
        look["position"] = [look["position"][0], override["y"]]
    for key in (
        "color",
        "outline_color",
        "box_color",
        "shadow_color",
    ):  # `#rrggbb` in the project; the style's alpha stays
        if key in override:
            look[key] = [*hex_rgb(override[key]), look[key][3] if len(look[key]) > 3 else 1.0]
    if "shadow_opacity" in override:
        look["shadow_color"] = [*look["shadow_color"][:3], override["shadow_opacity"]]
    if "box_opacity" in override:
        look["box_color"] = [*look["box_color"][:3], override["box_opacity"]]
    if "box_padding_x" in override or "box_padding_y" in override:
        x, y = look["box_padding"]
        look["box_padding"] = [override.get("box_padding_x", x), override.get("box_padding_y", y)]
    if "box_radius" in override:
        look["box_radius"] = override["box_radius"]
    for key in ("box", "uppercase"):
        if key in override:
            look[key] = bool(override[key])
    if (
        override.get("shadow_on") is False
    ):  # the switch keeps the shadow's size and colour for when it is turned on again
        look["shadow"] = 0
    elif override.get("shadow_on") and not look["shadow"]:
        look["shadow"] = override.get("shadow") or 4
    return look


def hex_rgb(value: str) -> list[float]:
    """`#rrggbb` → RGB floats (0 to 1)."""
    return [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]


def rgb_hex(rgba: list[float]) -> str:
    """RGB floats (0 to 1) → `#rrggbb`."""
    return "#" + "".join(f"{round(max(0.0, min(1.0, c)) * 255):02x}" for c in rgba[:3])


def ass_color(rgba: list[float]) -> str:
    """RGBA floats (0 to 1) → `&HAABBGGRR` (ASS alpha 00 is opaque)."""
    r, g, b, *rest = (max(0.0, min(1.0, float(c))) for c in rgba)
    a = rest[0] if rest else 1.0
    return "&H{:02X}{:02X}{:02X}{:02X}".format(*(round(v * 255) for v in (1 - a, b, g, r)))


def ass_time(seconds: float) -> str:
    """`H:MM:SS.cc` (centiseconds)."""
    total = max(0, round(seconds * 100))
    hours, rest = divmod(total, 360_000)
    minutes, rest = divmod(rest, 6_000)
    secs, cs = divmod(rest, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def escape(text: str) -> str:
    """Cue text → ASS text: no override braces or backslashes; line breaks become `\\N`."""
    clean = text.replace("\\", "/").replace("{", "(").replace("}", ")")
    return "\\N".join(line.strip() for line in clean.splitlines())


def animation_tags(animation: dict[str, Any]) -> str:
    """Override tags for the cue's entrance (`pop`: scale from → peak → 100 %)."""
    if animation.get("type") != "pop":
        return ""
    start, peak = animation.get("from", 70), animation.get("peak", 112)
    total = int(animation.get("ms", 170))
    middle = int(animation.get("peak_ms", round(total * 0.53)))
    return (
        f"\\fscx{start}\\fscy{start}"
        f"\\t(0,{middle},\\fscx{peak}\\fscy{peak})"
        f"\\t({middle},{total},\\fscx100\\fscy100)"
    )


def box_shape(text: str, style: dict[str, Any], font_size: int) -> str:
    """An ASS drawing of the rounded rectangle behind `text` (one or more lines) at `font_size`."""
    lines = [line.strip() for line in text.splitlines()] or [""]
    widest = max(fonts.text_width(line, style["font"], style["bold"], font_size) for line in lines)
    pad_x, pad_y = (p * font_size for p in style["box_padding"])
    w = round(widest + 2 * pad_x)
    h = round(len(lines) * font_size + 2 * pad_y)
    r = round(min(style["box_radius"] * font_size, w / 2, h / 2))
    return (
        f"m {r} 0 l {w - r} 0 b {w} 0 {w} 0 {w} {r} l {w} {h - r} b {w} {h} {w} {h} {w - r} {h} "
        f"l {r} {h} b 0 {h} 0 {h} 0 {h - r} l 0 {r} b 0 0 0 0 {r} 0"
    )


def style_fields(style: dict[str, Any], width: int, scale: float) -> list[Any]:
    """The values of an ASS `Style:` line (without its name) for a resolved look."""
    margin = round(width * (1 - style["width"]) / 2)
    return [
        style["font"],
        round(style["font_size"] * scale),
        ass_color(style["color"]),
        ass_color(style["color"]),
        ass_color(style["outline_color"]),
        ass_color(style["shadow_color"]),
        -1 if style["bold"] else 0,
        0,
        0,
        0,
        100,
        100,
        0,
        0,
        1,  # the rectangle is drawn as its own shape (rounded, padded), not ASS's BorderStyle 3
        round(style["outline"] * scale, 1),
        round(style["shadow"] * scale, 1),
        5,
        margin,
        margin,
        0,
        1,
    ]


def to_ass(
    cues: CueList,
    look: dict[str, Any] | None = None,
    size: tuple[int, int] | None = None,
    line_length: int | None = None,
) -> str:
    """The whole `.ass` file for these cues, drawn on a `size` (width, height) canvas.

    `look` is the track's resolved look; a cue's own `look` overrides it (ADR-022) and gets its
    own `Style:` line when it differs.
    """
    track = {**DEFAULT_LOOK, **(look or {})}
    width, height = size or DEFAULT_SIZE
    scale = min(width, height) / BASE_HEIGHT
    styles: dict[tuple, str] = {tuple(style_fields(track, width, scale)): "Default"}
    events: list[str] = []
    for cue in cues.cues:
        style = with_look(track, cue.look) if cue.look else track
        fields = tuple(style_fields(style, width, scale))
        name = styles.setdefault(fields, f"Cue{len(styles)}")
        x = round(style["position"][0] * width)
        y = round((1 - style["position"][1]) * height)
        animation = animation_tags(style["animation"])
        box = bool(style["box"])
        text = wrap_lines(cue.text, line_length)
        if style["uppercase"]:
            text = text.upper()
        times = f"{ass_time(cue.start)},{ass_time(cue.end)},{name},,0,0,0,,"
        if box:  # layer 0: the rectangle, with the same position and animation as the text above it
            shape = box_shape(text, style, fields[1])
            fill = ass_color(style["box_color"])
            events.append(
                f"Dialogue: 0,{times}{{\\an5\\pos({x},{y}){animation}\\bord0\\shad0"
                f"\\1c&H{fill[4:]}&\\1a&H{fill[2:4]}&\\p1}}{shape}{{\\p0}}"
            )
        events.append(
            f"Dialogue: {int(box)},{times}{{\\an5\\pos({x},{y}){animation}}}{escape(text)}"
        )
    lines = [
        "[Script Info]",
        "; Generated by Legendária (flosub) — https://github.com/flou-ainan/Legendaria",
        "ScriptType: v4.00+",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        *(f"Style: {name}," + ",".join(str(f) for f in fields) for fields, name in styles.items()),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        *events,
    ]
    return "\n".join(lines) + "\n"
