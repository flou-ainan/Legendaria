# Chat context (hand-off)

**Last updated:** 2026-10-27, by Claude Code (Sonnet 5.5), after step 33.
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

**Open and next**
- **Next:** plan 08 step 1 (contextual toolbar, 5 icons max) when the owner asks; the owner keeps testing (`cd engine && uv run flosub serve`) and sends more corrections; mobile polish comes later.
- **Known gaps:** touch dragging on the timeline, `.ass`/`.srt` import, fonts on Windows/macOS, an LLM pass in the review panel, cleaning old uploads, drive list on Windows.
- **Pending owner decisions:** import `.ass`/`.srt` + `flosub align --srt` (plan 04 §11.3, item 4).
- **Not published:** engine 0.1.0.dev4 is not on PyPI; the tag needs the owner's approval.
- **Open PRs:** #28 (docs for steps 28–30), #29 (steps 31–32, stacked on #28).

## Last two complete replies (verbatim)

### Reply 1 (2026-10-27): the owner's first corrections
> As 8 correções estão feitas. Para abrir: `cd engine && uv run flosub serve`, sem caminho.
>
> 1. **Sem caminho:** o editor abre numa tela inicial que pede o vídeo.
> 2. **Abrir ou arrastar:** "Escolher um arquivo…" abre um navegador de pastas dentro da página, com campo de caminho editável, e o vídeo abre onde está. Se você arrastar um vídeo para a página, ele é copiado para a pasta de dados da Legendária. O navegador não informa de onde o arquivo veio, e o servidor precisa do caminho real. Registrei isso na ADR-017.
> 3. **Listas suspensas:** modelo (com tamanho e se já está baixado), idioma e estilo.
> 4. **Glossário:** aba com glossário ativo, novo, adicionar palavra ou `errado -> certo`, importar um `.txt` e exportar. A revisão fica na mesma aba.
> 5. **Encaixe ao vivo:** o bloco gruda durante o arrasto, com uma linha-guia branca no alvo. Há um botão de ímã na barra de ferramentas abaixo do vídeo (atalho M).
> 6. **Layout:** vídeo em cima, barra de ferramentas com botões grandes, editor do bloco selecionado e timeline embaixo. Em tela estreita o painel lateral vira uma gaveta por baixo. Arrastar com o dedo na timeline não foi testado.
> 7. **Duplo clique edita:** seleciona o bloco e põe o cursor no texto (Esc sai da caixa). Dividir ficou na barra de ferramentas, no editor do bloco e na tecla S.
> 8. **Painel opcional:** a lista de legendas virou aba de uma gaveta (Legendas, Glossário, Cortes, Exportar), fechada por padrão.
>
> **Testes:** 127 do motor, 6 do app, o teste de navegador atualizado e o pre-commit passaram. Conferi capturas em tela larga e estreita.
>
> **Next task:** a próxima rodada de correções — tier: **standard** (Sonnet), effort: **low** a **medium**.

### Reply 2 (2026-10-27): round 2

> Feito: piscar da timeline, logo e favicon, "Português (Brasil / Portugal)", menu Arquivo (hambúrguer no celular), recuperação local (IndexedDB) com religar vídeo movido (mesma duração ±0,5 s e proporção ±1 %), idioma da interface en/pt-BR, plano 08 com o PDF de UX, CI (o e-mail era o erro de formatação do `workspace.py`, já corrigido).
>
> **Next task:** passo 1 do plano 08 (barra de ferramentas contextual) — tier: **standard** (Sonnet), effort: **medium**.
