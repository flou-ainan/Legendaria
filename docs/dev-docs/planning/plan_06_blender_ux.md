# Plan 06 — Blender user experience (draft)

**Status:** superseded by plan 07 (the Blender add-on is frozen, ADR-014)
**Date:** 2026-10-26

The owner found Blender's Video Sequencer hard to reach and to use: the add-on lives in a sidebar tab (N key) of the sequencer area, which a newcomer does not find on their own. Ideas to evaluate:

- **A one-click setup:** "Legendária → Set up" creates or switches to a workspace with the Video Editing layout. It opens the sequencer sidebar on the Legendária tab and sets the scene view transform to "Standard" (plan 04 §6.3).
- **Entry points:** a Legendária menu in the sequencer header and in File → Import ("Video with subtitles…"), so users do not need the N key.
- **A guided flow:** pick a video → it is added to the timeline → Generate → review → export or render, with short hints in the panel.
- **Fewer clicks:** auto-select the video strip after import; remember the last settings.
- **Launcher (owner idea, 2026-10-26):** a small executable/shortcut ("Legendária") that opens Blender directly with a preconfigured project: Video Editing layout, Standard colors, our tab open, an "Add video" prompt. Could ship with the installer (plan 01 phase 4), using a startup `.blend` template plus `blender --python` to apply the setup.
- **First real use (2026-10-26):** the owner ran the add-on successfully; the interface feels complex but is workable. The captions looked white instead of yellow, which was the AgX/Filmic color issue, fixed in step 16 by switching to Standard automatically.
- **A non-Blender path:** the web GUI of plan 05 is the simpler road for people who do not want an editor.

To be detailed after the owner tests the add-on.
