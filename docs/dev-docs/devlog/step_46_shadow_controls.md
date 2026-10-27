# Step 46 — Shadow controls

**Date:** 2026-10-27
**Related:** ADR-019

The Look menu has a Shadow checkbox and, when on, colour, size (0–20 px) and intensity (opacity). New look keys `shadow`, `shadow_on`, `shadow_color`, `shadow_opacity` (cleaned in `clean_look`, applied in `with_look`, in the schema, per cue too); `/api/state` `base` reports the style's shadow; API version 4 (restart the server). Tests: 136 pytest (shadow keys, on/off, clamping), e2e (colour and size reach the preview style, off writes 0).
