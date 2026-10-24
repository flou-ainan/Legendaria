# SPDX-License-Identifier: GPL-3.0-or-later
"""VSE API differences between Blender 4.2 and 5.x, detected by feature, not version.

Verified on 4.2.23 and 5.2.3:
- strip collections: `sequences` / `sequences_all` (4.x) → `strips` / `strips_all` (5.x)
- `new_effect(..., frame_end=)` (4.x) → `new_effect(..., length=)` (5.x)
- text alignment: `align_x` / `align_y` (4.x) → `alignment_x` + `anchor_x` / `anchor_y` (5.x)
"""

from __future__ import annotations


def top_strips(editor):
    """Top-level strips collection (supports `new_effect` and `remove`)."""
    return editor.strips if hasattr(editor, "strips") else editor.sequences


def all_strips(editor):
    """All strips, including those inside meta strips."""
    return editor.strips_all if hasattr(editor, "strips_all") else editor.sequences_all


def new_text_strip(editor, name: str, channel: int, frame_start: int, frame_end: int):
    """Create a TEXT effect strip covering [frame_start, frame_end)."""
    coll = top_strips(editor)
    params = coll.bl_rna.functions["new_effect"].parameters
    length = max(1, frame_end - frame_start)
    if "length" in params:
        return coll.new_effect(
            name=name, type="TEXT", channel=channel, frame_start=frame_start, length=length
        )
    return coll.new_effect(
        name=name,
        type="TEXT",
        channel=channel,
        frame_start=frame_start,
        frame_end=frame_start + length,
    )


def remove_strip(editor, strip) -> None:
    """Delete a strip."""
    top_strips(editor).remove(strip)


def set_alignment(strip, align_x: str = "CENTER", align_y: str = "CENTER") -> None:
    """Horizontal/vertical text alignment around the strip's location."""
    props = strip.bl_rna.properties
    if "align_x" in props:  # 4.x
        strip.align_x = align_x
        strip.align_y = align_y
        return
    if "alignment_x" in props:  # 5.x
        strip.alignment_x = align_x
    if "anchor_x" in props:
        strip.anchor_x = align_x
        strip.anchor_y = align_y


def set_if_present(strip, name: str, value) -> bool:
    """Set a property when this Blender version has it; returns whether it was set."""
    if name in strip.bl_rna.properties:
        setattr(strip, name, value)
        return True
    return False


def media_path(strip) -> str:
    """Absolute file path of a MOVIE or SOUND strip ('' for other types)."""
    import bpy

    if strip.type == "MOVIE":
        return bpy.path.abspath(strip.filepath, library=strip.id_data.library)
    if strip.type == "SOUND" and strip.sound:
        return bpy.path.abspath(strip.sound.filepath, library=strip.sound.library)
    return ""
