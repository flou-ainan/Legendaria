"""The fonts bundled with Legendária (open licence), listed in `fonts/fonts.json`."""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
from functools import lru_cache
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parent / "fonts"


def catalog() -> list[dict[str, object]]:
    """The bundled families: `family`, `file`, `bold` (the file is the bold cut), `category`."""
    return json.loads((FONTS_DIR / "fonts.json").read_text(encoding="utf-8"))


def file_for(family: str) -> Path | None:
    """The bundled font file for `family` (case-insensitive), or None."""
    for entry in catalog():
        if str(entry["family"]).lower() == family.lower():
            return FONTS_DIR / str(entry["file"])
    return None


def find_font(name: str, bold: bool) -> Path | None:
    """The font file the system uses for `name` (fontconfig), so the preview matches FFmpeg."""
    tool = shutil.which("fc-match")
    if not tool:
        return None
    pattern = f"{name}:bold" if bold else name
    result = subprocess.run(
        [tool, "-f", "%{file}", pattern], capture_output=True, text=True, check=False
    )
    path = Path(result.stdout.strip()) if result.returncode == 0 else None
    return path if path and path.is_file() else None


@lru_cache(maxsize=32)
def metrics_for(family: str, bold: bool) -> FontMetrics | None:
    """Advance widths of `family` (bundled first, then the system's), or None when no file is found."""
    path = file_for(family) or find_font(family, bold)
    try:
        return FontMetrics(path.read_bytes()) if path else None
    except (OSError, ValueError, struct.error):
        return None


def text_width(text: str, family: str, bold: bool, size: float) -> float:
    """Width in pixels of one line of `text` drawn at ASS font `size` (no kerning; a guess without the file)."""
    metrics = metrics_for(family, bold)
    if metrics is None:
        return 0.55 * size * len(text)
    return metrics.width(text) * size


class FontMetrics:
    """Just enough of a TrueType/OpenType file to measure text: cmap, hmtx and the line height."""

    def __init__(self, data: bytes) -> None:
        start = (
            struct.unpack_from(">I", data, 12)[0] if data[:4] == b"ttcf" else 0
        )  # first font of a collection
        count = struct.unpack_from(">H", data, start + 4)[0]
        tables = {}
        for i in range(count):
            tag, _, offset, _ = struct.unpack_from(">4sIII", data, start + 12 + 16 * i)
            tables[tag.decode("latin-1")] = offset
        hhea, hmtx = tables["hhea"], tables["hmtx"]
        metrics = struct.unpack_from(">H", data, hhea + 34)[0]
        self.advances = [struct.unpack_from(">H", data, hmtx + 4 * i)[0] for i in range(metrics)]
        if (
            "OS/2" in tables
        ):  # libass (like VSFilter) makes the font size equal to winAscent + winDescent
            ascent, descent = struct.unpack_from(">HH", data, tables["OS/2"] + 74)
        else:
            ascent, descent = struct.unpack_from(">hh", data, hhea + 4)
            descent = -descent
        self.height = (ascent + descent) or struct.unpack_from(">H", data, tables["head"] + 18)[0]
        self.glyphs = self._cmap(data, tables["cmap"])

    @staticmethod
    def _cmap(data: bytes, cmap: int) -> dict[int, int]:
        """Character → glyph index, from the format 12 (full Unicode) or format 4 (BMP) subtable."""
        count = struct.unpack_from(">H", data, cmap + 2)[0]
        subtables = {}
        for i in range(count):
            platform, encoding, offset = struct.unpack_from(">HHI", data, cmap + 4 + 8 * i)
            subtables[(platform, encoding)] = cmap + offset
        glyphs: dict[int, int] = {}
        for key in ((3, 10), (0, 4), (3, 1), (0, 3), (0, 1), (0, 0)):
            if key not in subtables:
                continue
            at = subtables[key]
            fmt = struct.unpack_from(">H", data, at)[0]
            if fmt == 12:
                groups = struct.unpack_from(">I", data, at + 12)[0]
                for g in range(groups):
                    first, last, glyph = struct.unpack_from(">III", data, at + 16 + 12 * g)
                    for char in range(first, min(last, 0x2FFFF) + 1):
                        glyphs[char] = glyph + char - first
                return glyphs
            if fmt == 4:
                segments = struct.unpack_from(">H", data, at + 6)[0] // 2
                ends = at + 14
                starts = ends + 2 * segments + 2
                deltas = starts + 2 * segments
                ranges = deltas + 2 * segments
                for s in range(segments):
                    end, first = (
                        struct.unpack_from(">HH", data, ends + 2 * s)[0],
                        struct.unpack_from(">H", data, starts + 2 * s)[0],
                    )
                    delta = struct.unpack_from(">h", data, deltas + 2 * s)[0]
                    offset = struct.unpack_from(">H", data, ranges + 2 * s)[0]
                    for char in range(first, end + 1):
                        if char == 0xFFFF:
                            continue
                        if offset == 0:
                            glyph = (char + delta) & 0xFFFF
                        else:
                            where = ranges + 2 * s + offset + 2 * (char - first)
                            glyph = struct.unpack_from(">H", data, where)[0]
                            glyph = (glyph + delta) & 0xFFFF if glyph else 0
                        glyphs[char] = glyph
                return glyphs
        return glyphs

    def width(self, text: str) -> float:
        """Advance width of `text` as a fraction of the ASS font size."""
        last = self.advances[-1]
        total = 0
        for char in text:
            glyph = self.glyphs.get(ord(char), 0)
            total += self.advances[glyph] if glyph < len(self.advances) else last
        return total / self.height
