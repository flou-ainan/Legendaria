# Step 42 — Look: colours, rectangle, caps; compact toolbar buttons

**Date:** 2026-10-27
**Related:** ADR-019

- The Look menu gained text colour, outline colour, "Rectangle behind the text" and "ALL CAPS" checkboxes. They are project `look` overrides (`color`, `outline_color`, `box`, `uppercase`), validated in `project.clean_look`, applied by `ass.with_look`, so the preview, `.ass` and burned MP4 agree. Reset clears them. The server sends the style's own values in `base`, so the controls show the real current state.
- **Why the text was all caps:** the "pop" style sets `uppercase: true` in the config. It stays the default for pop (owner's choice); the ALL CAPS checkbox now turns it off per project.
- Toolbar buttons are fixed squares with the icon centred (the label space is gone).
- Tests: 132 pytest (colour/box/caps cleaning, `with_look`, caps off), svelte-check, Vitest, e2e; screenshot checked.
