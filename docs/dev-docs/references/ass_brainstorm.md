# .ass (Advanced SubStation Alpha) brainstorm (summary)

> A summary of the owner's conversation with Google Gemini (2026-10-26) about `.ass` subtitles, with the claims checked on the dev machine. It feeds plan 04 and ADR-012.

## What `.ass` can do

- **Typography:** any font, size, weight, italic.
- **Colors:** four color layers (primary, secondary used by karaoke, outline, shadow/box), each with its own alpha.
- **Position:** numpad alignment (`\an1–9`), absolute position (`\pos`), movement (`\move`), scale (`\fscx`/`\fscy`), spacing, 2D/3D rotation (`\frz`, `\frx`, `\fry`).
- **Effects:** outline width (`\bord`), shadow (`\shad`), blur (`\blur`, `\be`), opaque box style.
- **Masks and drawing:** clipping (`\clip`) and vector drawings (`\p1`).
- **Animation:** any property animated over time (`\t(t1,t2,…)`), fades (`\fad`).
- **Karaoke:** `\k`, `\kf` (progressive fill), `\ko`, timed in centiseconds.
- **CapCut look:** word-by-word highlighting is karaoke; the word "pop" is `\t` on scale. For example, per word: `{\kf32\t(0,80,\fscx118\fscy118)\t(80,160,\fscx100\fscy100)}WORD`.

## Ecosystem

- **libass** renders `.ass` in mpv, VLC, FFmpeg and HandBrake.
- **FFmpeg burns subtitles in** with `-vf ass=file.ass` or `subtitles=`.
- **Aegisub** (with community forks) is the classic open-source `.ass` editor: powerful, but its UI is dated (the owner's main complaint). **Subtitle Edit** handles conventional subtitles.
- **Kdenlive** uses `.ass` internally for its subtitle track but understands only basic tags: bold, italic, color, outline, simple position. No `\t`, `\move`, 3D, `\p`, karaoke or `\clip` (claim from the conversation; still to be checked by us).
- **The Blender VSE** has no native `.ass` support. Community add-ons import text and timing into text strips and drop most styling. A text strip has one style, which means no multi-color text inside one strip, no per-character transforms and no blur.

## Ideas proposed for Legendária

1. **`.ass` export from the engine** (`to_ass(cues, preset)`): header, styles, and events with karaoke and pop tags built from the word timings.
2. **High-fidelity preview in Blender:** render the subtitles alone with libass to a video with an alpha channel, and put it above the footage in the VSE.
3. **Native hybrid in Blender:** keep text strips for editing, with a per-word strip and keyframe approach for the CapCut look; export `.ass` with the rich tags.
4. **Align existing subtitles:** take an `.srt` with block timings and get word timings from the audio (the conversation suggested wav2vec2/WhisperX forced alignment).
5. **`.ass` import into Blender** (a light parser: styles and dialogue, basic tags mapped to text strips).
6. **Final burn-in with FFmpeg + libass**, pixel-perfect.

## Checked on the dev machine (2026-10-26)

- The local FFmpeg 4.4 has the `ass` and `subtitles` filters (libass) and the alpha-capable encoders `qtrle`, `prores_ks`, `png` and `libvpx-vp9`.
- An `.ass` built from real cues (the owner's crochet video, captions style) with `\kf` plus `\t` pop and a Montserrat bold style, rendered by FFmpeg onto a transparent 1080×1920 canvas to **QuickTime Animation (qtrle, argb)**, keeps a real alpha channel. The progressive karaoke fill mid-word renders correctly.
- In **Blender 4.2.23 and 5.2.3**, that `.mov` as a movie strip with `blend_type = ALPHA_OVER` composites correctly over a color strip: the same frame as FFmpeg.
- **Color management caveat:** with the default view transform (Filmic in 4.2, AgX in 5.x), colors in the VSE output are tone-mapped (the yellow came out khaki). Video work needs `view_transform = "Standard"`. This also affects the add-on's current text strips.

## Corrections to the conversation

- No Python libass bindings are needed: FFmpeg's `ass` filter covers both rendering paths (the overlay and the burn-in).
- For aligning an existing `.srt`, a cheaper first option than wav2vec2: transcribe with word timings, then align the SRT text to the transcribed words with a text diff. This reuses the re-alignment of plan 03 (`review/align.py`). WhisperX stays as a fallback in the backlog.
