# SPDX-License-Identifier: GPL-3.0-or-later
"""Cues ↔ text strips: create caption strips, find the ones we made, read them back."""

from __future__ import annotations

import json
from pathlib import Path

from . import compat, timecode
from .engine_bridge import user_config_dir

TAG = "legendaria_cue"  # custom property marking strips created by the add-on
WORDS = "legendaria_words"  # word timings (JSON) kept for later animation
PRESETS_DIR = Path(__file__).resolve().parent / "presets"


def scene_fps(scene) -> float:
    """Real frames per second (fps / fps_base)."""
    return scene.render.fps / (scene.render.fps_base or 1.0)


def load_preset(style: str) -> dict:
    """Strip style for a cue style: user override in the config dir, else the shipped preset."""
    for folder in (user_config_dir() / "presets", PRESETS_DIR):
        path = folder / f"{style}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return json.loads((PRESETS_DIR / "captions.json").read_text(encoding="utf-8"))


def apply_preset(strip, preset: dict, resolution_y: int) -> None:
    """Apply a style preset to a text strip; font sizes are scaled from 1080 px."""
    scale = resolution_y / 1080 if resolution_y else 1.0
    if "font_size" in preset:
        strip.font_size = preset["font_size"] * scale
    if "location" in preset:
        strip.location = preset["location"]
    compat.set_alignment(strip, preset.get("align_x", "CENTER"), preset.get("align_y", "CENTER"))
    for key in (
        "wrap_width",
        "color",
        "use_bold",
        "use_outline",
        "outline_color",
        "outline_width",
        "use_shadow",
        "shadow_color",
        "use_box",
        "box_color",
        "box_margin",
    ):
        if key in preset:
            compat.set_if_present(strip, key, preset[key])


def is_ours(strip) -> bool:
    """True for strips created by the add-on."""
    return strip.type == "TEXT" and TAG in strip


def overlaps(strip, frame_start: int, frame_end: int) -> bool:
    """Whether the strip's visible range intersects [frame_start, frame_end)."""
    return strip.frame_final_start < frame_end and strip.frame_final_end > frame_start


def tagged_in_range(
    editor, channel: int, frame_start: int, frame_end: int, by_midpoint: bool = False
) -> list:
    """Our caption strips on `channel` in the range (they would be replaced).

    By default any overlap counts; with `by_midpoint` only strips whose middle frame is
    inside the range (the rule used when regenerating part of a video).
    """

    def inside(s) -> bool:
        if by_midpoint:
            return frame_start <= (s.frame_final_start + s.frame_final_end) / 2 < frame_end
        return overlaps(s, frame_start, frame_end)

    return [
        s for s in compat.top_strips(editor) if s.channel == channel and is_ours(s) and inside(s)
    ]


def foreign_in_range(editor, channel: int, frame_start: int, frame_end: int) -> list:
    """Strips not made by us on `channel` in the range (we never touch these)."""
    return [
        s
        for s in compat.top_strips(editor)
        if s.channel == channel and not is_ours(s) and overlaps(s, frame_start, frame_end)
    ]


def pick_channel(editor, media_strip, frame_start: int, frame_end: int) -> int:
    """First channel above the media strip that holds only our captions (or nothing) in range."""
    channel = media_strip.channel + 1
    while channel < 128 and foreign_in_range(editor, channel, frame_start, frame_end):
        channel += 1
    return channel


def media_range(media_strip) -> tuple[int, int, int]:
    """(content_start, visible_start, visible_end) frames of a MOVIE/SOUND strip.

    Second 0 of the media is at `frame_start`; trimming moves only the visible range.
    """
    return int(media_strip.frame_start), media_strip.frame_final_start, media_strip.frame_final_end


def load_cues(path: Path) -> dict:
    """Read a cues JSON (v1) written by `flosub ... --format cues`."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("version") != 1:
        raise ValueError(f"Unsupported cues version {data.get('version')!r}")
    return data


def create_strips(
    scene, editor, cues: list[dict], media_strip, channel: int, style: str, frame_range=None
) -> list:
    """Replace our strips on `channel` with new cue strips; returns the new strips.

    Without `frame_range` the whole visible (trimmed) part of the media is replaced.
    With `frame_range=(start, end)` only captions whose middle falls in the range are
    replaced, and new strips are trimmed so they never overlap the captions kept around it.
    """
    fps = scene_fps(scene)
    content_start, visible_start, visible_end = media_range(media_strip)
    if frame_range:
        low, high = max(frame_range[0], visible_start), min(frame_range[1], visible_end)
        old = tagged_in_range(editor, channel, low, high, by_midpoint=True)
    else:
        low, high = visible_start, visible_end
        old = tagged_in_range(editor, channel, low, high)
    for strip in old:
        compat.remove_strip(editor, strip)
    kept = [
        (s.frame_final_start, s.frame_final_end)
        for s in tagged_in_range(editor, channel, visible_start, visible_end)
    ]
    preset = load_preset(style)
    created = []
    for index, cue in enumerate(cues, start=1):
        start = max(timecode.seconds_to_frame(cue["start"], fps, content_start), visible_start)
        end = min(timecode.seconds_to_frame(cue["end"], fps, content_start), visible_end)
        if frame_range and not low <= (start + end) / 2 < high:
            continue
        for kept_start, kept_end in kept:  # never overlap captions that stay
            if kept_start < end and kept_end > start:
                if kept_start <= start:
                    start = kept_end
                else:
                    end = kept_start
        if end <= start:
            continue
        strip = compat.new_text_strip(editor, f"LGD {index:04d}", channel, start, end)
        strip.text = cue["text"]
        strip[TAG] = index
        strip[WORDS] = json.dumps(cue.get("words", []), ensure_ascii=False)
        apply_preset(strip, preset, scene.render.resolution_y)
        created.append(strip)
        kept.append((start, end))  # later cues must not overlap this one either
    return created


def selected_caption_range(editor) -> tuple[int, int] | None:
    """Frame span of the selected caption strips, or None when none is selected."""
    chosen = [s for s in compat.top_strips(editor) if is_ours(s) and s.select]
    if not chosen:
        return None
    return min(s.frame_final_start for s in chosen), max(s.frame_final_end for s in chosen)


def read_cues(
    scene, editor, channel: int, only_ours: bool = True
) -> list[tuple[float, float, str]]:
    """Text strips on `channel` as (start_s, end_s, text) from frame 0, sorted by time.

    Uses the add-on's strips when there are any; otherwise every text strip on the channel.
    """
    fps = scene_fps(scene)
    texts = [s for s in compat.top_strips(editor) if s.channel == channel and s.type == "TEXT"]
    ours = [s for s in texts if is_ours(s)]
    chosen = ours if (only_ours and ours) else texts
    chosen.sort(key=lambda s: s.frame_final_start)
    start_frame = scene.frame_start
    return [
        (
            timecode.frame_to_seconds(s.frame_final_start, fps, start_frame),
            timecode.frame_to_seconds(s.frame_final_end, fps, start_frame),
            s.text,
        )
        for s in chosen
    ]
