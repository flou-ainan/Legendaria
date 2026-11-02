# Chat context (hand-off)

**Last updated:** 2026-11-02, by Claude Code (Opus 5.5), after step 62 (network access built).
**Policy:** `AGENTS.md` and `docs/dev-docs/README.md` ("chat-context.md"). This is a snapshot that gets replaced, never appended. It is public: no secrets and no private data.

## Summary of the conversation so far

**Who and how**
- The owner (GitHub `flou-ainan`) chats in Brazilian Portuguese, so agents reply in Portuguese.
- Dev docs and code are in English. User-facing text is in en + pt-BR.
- The owner tests manually and then gives feedback. They prefer lean MVPs with "later" notes, and want options plus a recommendation before a decision.
- They avoid heavy frameworks and libraries.
- Public actions need explicit approval every time: PyPI tags, releases, and anything published.
- At the end of each task, the agent says which model tier and effort the next task needs (owner prefers low/medium; high only with a reason). Rule in `AGENTS.md`, "Recommending the model for the next task".
- `main` is protected: every change goes through a branch, a PR, the `ci` check and a squash merge.

**Project:** Legendária (repo `flou-ainan/Legendaria`).
- An open-source, CapCut-style automatic subtitle creator.
- The engine is the CLI `flosub` (PyPI package `legendaria`, MIT): faster-whisper transcription, glossary and review, cues, styles, `.ass` export, and burn/overlay with FFmpeg.

**History, condensed**
1. **Plans 01–03:** engine + Blender add-on MVP; glossary library and review; an experimental LLM reviewer (off by default).
2. **Plan 04 MVP subset (step 23):**
   - `.ass` export with the "one-word pop" look; `flosub burn` / `overlay`;
   - in Blender, "Export ASS" and "Exact preview".
   - ADR-012: `.ass` + libass.
3. **Text capability tests in Blender:** the pop is done by `font_size`. ADR-013 (Blender 5.2 minimum) was accepted, then suspended.
4. **Owner's manual test** (2026-10-26):
   - glossaries are stored in `~/.config/legendaria/glossaries/`;
   - the `base` model works but is weak, so `small` is the minimum for Portuguese;
   - the desktop froze from RAM pressure (Blender's VSE cache plus browsers, with 2 GB of swap), recorded as KI-001;
   - editing caption strips in Blender is hard.
5. **Pivot (ADR-014, plan 07, step 28):** the Blender add-on is **frozen** (bug fixes only, probably retired later). A **local web editor** becomes the main UI, with three jobs:
   - cut the video (MVP: remove ranges only);
   - edit the subtitles;
   - export a burned MP4 or SRT/VTT/ASS.
   - The backend `flosub serve` (local Python + native FFmpeg) is always present; a standalone PWA is out of scope for now.
6. **Phase 0 spikes (step 29, `references/plan07_phase0_spikes.md`):**
   - JASSUB (libass in WASM) matches FFmpeg frame by frame, including the pop;
   - wavesurfer.js handles 500 cues, with peaks computed on the server (53 ms, 9 MB);
   - one-pass FFmpeg cut + burn with a cue remap works and stays in sync;
   - OpenReel gives patterns, not code.
   - The spike files live outside the repo in `../legendaria-spikes/` (they use the owner's media).
7. **Framework (ADR-015, 2026-10-27): Svelte 5 + Vite + TypeScript.** The owner chose it over Vue and React after their own research. They do not know Svelte well yet, so the code should stay simple and point to the docs.
8. **Step 30 (2026-10-27):**
   - READMEs updated for the browser editor;
   - OpenReel dissected (`references/openreel_dissection.md`): snapshot undo with auto-grouping, pixel-threshold snapping (plus word boundaries), a JSON shortcut table, zoom-at-cursor, a versioned and validated project file, property-based tests;
   - this hand-off file and its policy added.

9. **Step 31 (2026-10-27), PR #29 (stacked on #28):**
   - ADR-016: the project file `<video>.legendaria.json` (own JSON, kept ranges + cues in source time; `.ass`/SRT/VTT are exports). This answers the owner's earlier question about `.ass` vs extended `.ass`.
   - engine: `project.py`, `media.render` (one-pass cut + burn), `flosub serve` (stdlib server);
   - `web/`: transcribe, JASSUB live preview, cuts (I/O/X, restore), cue list, undo/redo, autosave, export MP4/SRT/VTT/ASS, en + pt-BR;
   - tested: 120 pytest, Vitest, a local Playwright run, a real transcription through the server.
   - New `AGENTS.md` rule for model recommendations.

10. **Step 32 (2026-10-27), same PR #29:** timeline with waveform from server peaks, draggable cue blocks, snapping, zoom; glossary review panel; Playwright smoke test in CI; fixed the ruff errors that made `checks` fail on step 31. The owner switched to Sonnet for this step and asked for the command to open their real video; they have notes and will start requesting edits once the MVP is finished.

11. **Step 33 (2026-10-27), same PR #29:** the owner's first 8 corrections: `flosub serve` with no path (file browser + drop, ADR-017), drop-down lists, glossary tools, live snapping with a magnet button, double-click edits, optional side drawer, a Kdenlive/CapCut-style layout. The owner wants the desktop to look like Kdenlive, with CapCut/InShot-style strong editing elements so mobile can follow later.

12. **Step 34 (2026-10-27), same PR #29:** round 2: fixed the timeline flicker (implicit grid column sized by the waveform; the e2e now samples it), logo and favicon, "Português (Brasil / Portugal)", File menu (hamburger on narrow screens), IndexedDB recovery copy and relinking a moved video (owner chose: same duration ±0.5 s and screen proportion ±1 %, ADR-018), interface language en/pt-BR from the menu, plan 08 from the owner's UX PDF.

13. **Step 35 (2026-10-27), same PR #29:** the owner asked for priority changes before the UX-study items: a quick **Look menu** (size and height sliders, Top / Bottom presets, font), **more fonts**, **translations as plain files**, and a **mobile toolbar** that slides sideways in one row. Done: project `look` override and 19 bundled OFL fonts picked from `~/.local/share/fonts` (ADR-019), locale files auto-discovered with a translators' guide and a test, mobile toolbar. Plan 08 reordered: this is "priority round 3", then the contextual toolbar, orange track, generate-captions sheet, per-cue style.

14. **Step 36 (2026-10-27), same PR #29:** the owner asked to remove the permanent tips (an interactive tutorial comes after the MVP) and to continue: plan 08 step 1 done, a contextual toolbar (5 tools max, changes with the selection).

15. **Step 37 (2026-10-27), same PR #29:** owner's corrections: touch scrolling on the timeline moved and resized blocks, so only the selected block can be dragged now; the snap stuck far from the pointer, so it is a real magnet now (keeps the pointer's position apart from the drawn one); Undo/Redo first in the toolbar; Solar Linear icons (ADR-020, CC BY 4.0).

16. **Step 38 (2026-10-27), same PR #29:** `settings.json` (basic/advanced, snap 4 px), toolbar without labels and dark selected icons, draggable playhead arrow and a centred-playhead mode for touch screens (ADR-021).

17. **Step 39:** playhead fixes: overlay arrow above the timeline, no jitter, blocks drawn left of the line (empty start by `transform`, not margins).

18. **Step 40:** orange subtitle blocks, grey-blue cuts, blue mark.

19. **Step 41:** Generate captions sheet (File menu), keeps cuts and look when regenerating.

20. **Step 42:** Look menu: text and outline colour, rectangle, ALL CAPS checkbox (pop stays caps by default); square toolbar buttons.

21. **Step 43:** colours seemed broken because the owner's server predated step 42; added an API version check with a restart banner, a heading in the Look menu, e2e coverage. Owner switched to Opus.

22. **Step 44:** rounded, padded rectangle drawn as its own shape (colour, transparency, width, height, roundness), outline colour and thickness, full screen keeps subtitles, "Edit this track's subtitles" (multiple tracks noted in plan 08).

23. **Step 45 (plan 09, ADR-022):** style per subtitle: Look menu "Whole track | This subtitle", "Apply to all", ✦ on blocks with their own style.

24. **Step 46:** shadow controls (on/off, colour, size, intensity) in the Look menu.

25. **Step 47:** breakpoint 1024 px, bottom sheets that slide up (drawer, Look), pinch zoom on the timeline.

26. **Step 48:** sheets take at most 44 % of the screen and the video stays pinned above them.

27. **Step 49:** robust full-screen sizing after a rotation (to confirm on the phone); a tall video is cropped to the part with the subtitles when a sheet is open.

28. **Steps 50–56 (2026-10-28):** phone testing through tunnels. Fixes: pinch zoom jump, squashed letters on 9:16 (JASSUB canvas size), unreachable end of the video in centred mode, a notice as soon as the video is missing. Plan 08 desktop extras: subtitle list open by default with search and replace, right-click menu on blocks, Ctrl+B split.
29. **Steps 57–58 (plan 11, ADR-023):** one server session per browser (cookie `legendaria_client`, API version 5); open a video from the computer's files or from the device; "Save to this device" after an export.
30. **Step 59 (plan 11, A):** a video picked on the device is played from the device (object URL), not streamed back; kept only until a reload (OPFS is the open part).
31. **Access decisions (ADR-024, plan 12, owner 2026-10-28):** the focus is local use, with the phone as another screen. ngrok ran out of bandwidth, so Tailscale is the recommended way away from home (private network, `tailscale serve` for HTTPS). LAN is the default and needs no third party. An own user name and password is required once the server listens beyond localhost. Headscale is only mentioned. After the MVP: reorganize, slim down, and an end-user installer ("next > next").

32. **Plans 13 and 14, ADR-025 (2026-10-29):** `ROADMAP.md` became the one list of pending work. Plan 13 proposed cloning CapCut / InShot; plan 14 and ADR-025 proposed plain subtitle lines with effects on top.
33. **House in order (2026-10-31, plan 15, step 60):** the owner found the plans messy and "clone CapCut" too vague. It is now a direction in `AGENTS.md`, not a plan. The focus is tying together what works, then the owner's list of corrections. Plan 14 is parked. Lint errors that failed PR #29 are fixed.

34. **Access decision (2026-11-02, ADR-026, plan 12):** the owner wants ease of use, hackable, modular and robust above all. LAN is the default but only once a password is set (no password: localhost only). The password applies to every non-local access, tunnels, Tailscale and Headscale included, because a guest on the Wi-Fi must not reach the computer's files. It is set the first time the app runs (a generator helps), stored hashed in a settings JSON (`access.json`), and shared by LAN, Tailscale and Headscale. A small tkinter launcher shows a splash, asks for the password on first run (and on every run until set), opens the browser, and has an (i) balloon linking to an en + pt-BR network doc. READMEs carry a summary and link to it. Remote clients cannot browse the computer's disk. Plain HTTP on the LAN is a stated limit; optional HTTPS comes later. The owner then authorized the push and the merge: #28 and #29 are in `main` (2026-11-02).
35. **Network access built (2026-11-02, step 62, plan 12):** `access.py`, the deny-by-default gate, `flosub auth`, the web sign-in and Access dialog, the `legendaria` tkinter launcher, and the guide `docs/network-access.md` (+ pt-BR). The owner said they will test it by hand and suggest what to change.
36. **Correction (2026-11-02):** the first version stopped a signed-in phone from browsing the computer's files. The owner wants the opposite: with the password, the phone opens the computer's videos. Now it can; `remote_browse: false` in `access.json` limits other devices to uploads. The password is what keeps visitors out. The owner tested through their Tailscale name with a throwaway server and password in an isolated config.
- **Next:** the owner tests network access by hand (launcher, phone on the Wi-Fi, then Tailscale) and sends corrections.
- **Then:** the owner sends the list of what is not good yet. No new features before that; everything else is parked in `ROADMAP.md`.
- **Not published:** engine 0.1.0.dev4 is not on PyPI; tags and releases need the owner's approval. Work happens on branch `feat/network-access`.

## Last two complete replies (verbatim)

### Reply 1 (2026-11-02): the access design, committed

> Fiz três commits na branch `feat/web-editor-mvp`, só com docs e a correção de lint. Não dei push nem merge, porque você só autorizou os commits.
>
> **Como ficou o desenho (ADR-026):**
> - Sem senha, o servidor escuta só em `127.0.0.1`. Com senha definida, a LAN passa a ser o padrão.
> - Senha para qualquer acesso que não seja este computador: LAN, Tailscale, Headscale e túneis (reconhecidos pelos cabeçalhos do proxy). No próprio computador a senha não é pedida, com uma opção para exigi-la.
> - Convidado do Wi-Fi não navega no disco: quem acessa de fora só envia um vídeo do próprio aparelho e baixa as próprias exportações.
> - Uma única checagem roda antes de qualquer rota; senha gerada tipo `k7mq-x2vd-9tpr`, guardada como hash scrypt em `access.json`; bloqueio por tentativas erradas até 15 minutos; endereços públicos recusados.
> - Launcher em tkinter com splash, pergunta da senha na primeira vez (e em toda execução até ser definida) e um balão (i) que liga ao guia em inglês ou português.
>
> **Um limite:** na LAN o tráfego é HTTP puro, então a senha pode ser vista por quem capturar o tráfego do mesmo Wi-Fi. O guia diz isso, com duas saídas: Wi-Fi de visitantes com isolamento, ou Tailscale/Headscale. HTTPS opcional entra depois.
>
> **Next task:** plano 12, passo 1 (`access.py` e seus testes) — tier: top, effort: medium — código sensível de segurança, mas o modelo de ameaças já está no ADR-026.

### Reply 2 (2026-11-02): network access built, PR #30

> O acesso pela rede está pronto e aberto como PR #30 (`feat/network-access`). Não dei merge: a sua autorização foi para o #28 e o #29, e este é código de segurança que você quer testar antes.
>
> **Estado do PR:** o `ci` passou em Linux, macOS e Windows. O GitGuardian reprovou, mas é falso positivo: ele marcou como "Generic Password" a mensagem de erro `"Too many wrong passwords."`. A única checagem obrigatória da `main` é o `ci`.
>
> **Para testar** (a partir da pasta `engine`): `uv run legendaria` abre a janela; `uv run flosub serve` é o caminho pelo terminal. Para sem senha, rode `flosub auth reset`. O guia `docs/network-access.md` tem os passos do Wi-Fi e do Tailscale.
>
> **Testado:** 225 testes do engine (incluindo a janela do launcher em display virtual), tipos e testes da web, e o e2e com um "celular" que entra com a senha, é barrado no navegador de arquivos e sai. Também quebrei o portão de propósito de quatro jeitos para ver se os testes pegavam: pegaram todos.
>
> **Não testado:** celular de verdade, uma rede Tailscale ou Headscale real (só simulei os cabeçalhos do `tailscale serve`), o launcher no Windows e no macOS, e os passos de firewall do guia.
>
> **Next task:** o seu teste manual (launcher, celular no Wi-Fi, depois Tailscale) e as correções — tier: standard, effort: medium — ajustes contra um desenho já escrito.
