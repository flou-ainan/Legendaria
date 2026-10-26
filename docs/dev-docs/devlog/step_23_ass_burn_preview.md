# Step 23 — `.ass` export, burn-in and exact preview (plan 04 §10, MVP subset)

**Date:** 2026-10-26
**Agent/author:** Claude Code (Opus 5.5), with flou-ainan

## What was done

The plan's scope was first added to `plan_04` as §10. ADR-012 is now accepted for this subset.

### Engine

- **`ass.py`** (new): cues → `.ass`.
  - One `Dialogue` per cue with `\an5\pos(x,y)`. With `pop`, the cue starts at `\fscx70\fscy70`, grows to 112 % by 90 ms and settles to 100 % by 170 ms. There is no karaoke (owner, plan 04 §8).
  - The look comes from the style's new `ass` block in the config, so it is hackable JSON: font, size at 1080 px, bold, RGBA colors (as in the add-on presets), outline, shadow, box (`BorderStyle 3`), position `[x, y from the bottom]`, line width, uppercase and animation.
  - Sizes scale with the **shorter side**, so a 1080×1920 video gets the same proportions as 1920×1080.
  - Braces and backslashes in the text cannot become override tags.
- **`media.py`** (new): FFmpeg support.
  - FFmpeg and ffprobe come from config `ffmpeg` (a file or a folder) or from PATH. When neither has them, the error says how to install FFmpeg.
  - `probe` reads the size, fps and duration, and swaps the size for rotated phone videos.
  - `burn` and `overlay` run FFmpeg with `-progress` and report `progress` events.
  - The `.ass` file is staged in a temp folder and passed by its bare name, so there is no filter-path escaping on Windows. Input and output paths are made absolute first.
- **Overlay recipe** (checked on FFmpeg 4.4): `color=c=black@0.0:s=WxH:r=FPS:d=DUR,format=rgba`, then `ass=subs.ass:alpha=1`, then `-c:v qtrle`.
  - Without `alpha=1`, the text has no alpha and the whole overlay is transparent.
- **CLI:**
  - `ass` format on `transcribe`, `export` and `review apply`. The canvas is the video's size, or `--size WxH`, or 1920×1080 for audio.
  - `export` accepts an edited **cues JSON**. The style comes from the file unless `--style` is given.
  - `flosub burn VIDEO [--subs FILE] [--style] [--output]` writes `VIDEO.subtitled.mp4`. The encoder arguments come from config `burn`; the default is H.264 CRF 18 with the audio copied. It refuses to overwrite the input.
  - `flosub overlay SUBS [--size --fps --duration --output]`.
  - Both take a transcript, a cues JSON or an `.ass`.
- **Config:**
  - `ass` blocks for `pop` (yellow, Arial bold 96, outline 6, shadow 4, uppercase, pop), `captions` (white, 76) and `subtitles` (white, 48, translucent box);
  - `ffmpeg` and `burn`;
  - schema and validation (`ass` must be an object; `animation.type` must be `none` or `pop`).

### Add-on

- **Export ASS** next to SRT/VTT. The strips are written as a cues JSON and sent to `flosub export --format ass --size <render size>`.
- **Exact preview** (`preview_ops.py`, new):
  - the strips go through `flosub overlay` in the background, with the scene's fps, size and duration, plus progress and cancel;
  - the movie goes on the first free channel above the captions with **Alpha Over**, and the captions channel is muted;
  - rendering the scene then gives the burned-in video;
  - each render gets its own file name, so Blender never shows cached frames of an old render. The old file is deleted when it is replaced or removed;
  - "Remove exact preview" deletes the movie and unmutes the captions.
- Preset font sizes now scale with the render's shorter side (`strips.short_side`), matching the engine.
- pt_BR for every new string.

### CI

- FFmpeg is installed in the Linux jobs, so the burn and overlay test really runs there. On macOS and Windows it is skipped when FFmpeg is missing.

## Files

- Engine:
  - new `legendaria_engine/ass.py`, `legendaria_engine/media.py` and `tests/test_ass.py`;
  - changed `cli.py`, `cues.py` (`CueList.from_dict`), `formats.py`, `config.py`, `defaults/config.json`, `schemas/config.schema.json` and `README.md`.
- Add-on: new `preview_ops.py`; changed `operators.py` (Export ASS, `render_size`, `export_ass`), `strips.py` (`short_side`, `write_cues_file`), `panel.py`, `__init__.py`, `locales/pt_BR.json`, `tests/blender_smoke.py`.
- `.github/workflows/ci.yml`.
- Docs: plan 04 (status, §10 and its DoD), ADR-012 (accepted for the subset), `PROJECT.md`, `CHANGELOG.md`.

## How it was tested

- Engine: 100 tests passed, 9 of them new, including a real burn and overlay on a synthetic clip. Ruff is clean.
- Add-on pytest: 35 passed. The i18n test passes.
- `blender_smoke.py` passed 33/33 on Blender 4.2.23 and 5.2.3, and 47/47 with `--real` on 5.2.3. The checks cover:
  - Export ASS: render size and pop tags;
  - the overlay is rendered and placed with Alpha Over above the captions;
  - the captions channel is muted;
  - Remove restores the strips and deletes the file.
- On the owner's crochet clip (the first 20 s, 24 fps), with the pop style:
  - the `.ass` matches the approved step 15 sample;
  - burn-in took 11 s and the overlay 5 s;
  - comparing the burned frame with the FFmpeg composite of the overlay at frame 42: 18 of 336,000 pixels in the caption area differ by more than 40, all on chroma edges;
  - a Blender 5.2.3 render with the overlay placed by `place_overlay` reproduces the overlay's pixels exactly.
- A first comparison seemed to show a thinner outline in Blender. The cause was a test overlay rendered at 30 fps for a 24 fps clip, which compared different frames. It was not a defect: the add-on always passes the scene's fps.
- Bug found and fixed: a relative `--output` was written inside FFmpeg's temp folder and lost. Paths are now absolute, and a regression test covers it.
- GUI walkthrough on Blender 4.2.23 (pt_BR): the panel shows "Prévia exata" and "Exportar ASS".

## Notes

- Fonts: the default is Arial, which exists on Windows and macOS; on Linux fontconfig maps it to Liberation Sans. Blender's text strips use Blender's own font, so only the exact preview shows the final font.
- The add-on presets and the engine `ass` blocks are separate definitions of a similar look. Plan 04 stage 4a (one shared preset schema) removes the duplication after the MVP.
