# Chat context (hand-off)

**Last updated:** 2026-10-27, by Claude Code (Opus 5.5), after step 31.
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

**Open and next**
- **Next:** the owner's manual test: `cd engine && uv run flosub serve <video>`.
- Then plan 07, step 32: waveform + draggable cues + snapping + zoom; review/glossary suggestions in the cue list; Playwright in CI (model recommendations are in plan 07, "Phase 2 progress").
- **Pending owner decisions:** import `.ass`/`.srt` + `flosub align --srt` (plan 04 §11.3, item 4).
- **Not published:** engine 0.1.0.dev4 is not on PyPI; the tag needs the owner's approval.
- **Open PRs:** #28 (docs for steps 28–30), #29 (step 31, stacked on #28).

## Last two complete replies (verbatim)

### Reply 1 (2026-10-27): Svelte chosen, OpenReel dissected, hand-off policy

> Fechado: **Svelte 5 + Vite + TypeScript**, registrado na ADR-015.
>
> Sobre a sua intuição: o Vue é simples, sim, e nasceu de uma ideia parecida com a do AngularJS. Mas o Svelte 5 é ainda mais próximo de HTML/JS puro, porque um componente é basicamente HTML com um `<script>` e um `<style>`. Para quem vem do React, o principal é aprender três "runes": `$state` (o estado), `$derived` (valores calculados) e `$effect` (efeitos). Vou manter os componentes simples e comentar onde usar cada um.
>
> **O que fiz**
> - **README** (inglês e pt-BR): fala do editor no navegador. Parti da edição que você tinha começado no README em inglês e espelhei no português. O Blender aparece como "congelado".
> - **ADR-015 e docs:** `PROJECT.md` (tabela de tecnologias e decisões) e plano 07 atualizados.
> - **Dissecação do OpenReel** (`docs/dev-docs/references/openreel_dissection.md`). Vamos aproveitar as ideias, sem copiar código:
>   - **Desfazer** que junta numa só etapa as mudanças rápidas no mesmo bloco, como um arraste.
>   - **Encaixe (snap)** com limite em pixels, que funciona igual em qualquer zoom. A gente ganha um extra que ele não tem: encaixar no início e no fim de cada **palavra** da transcrição.
>   - **Atalhos** numa tabela, que no nosso caso fica num JSON editável: espaço, setas, I/O para marcar o corte, S para dividir, Q/W, Delete, Ctrl+Z, N, Ctrl+=/−, `?`.
>   - **Zoom com Ctrl+roda** mantendo fixo o ponto sob o mouse, e a timeline seguindo o playhead.
>   - **Arquivo de projeto com versão e validação**, que vira a base da ADR-016.
>   - **Testes com entradas aleatórias** para os cortes.
>   - Ficam de fora: decodificação própria, exportação no navegador, React e multitrilhas.
> - **Nova regra no AGENTS.md:** o `docs/dev-docs/chat-context.md`, com um resumo enxuto da conversa e as minhas duas últimas respostas completas. Ele é atualizado quando você pedir, ou a cada algumas horas de trabalho, e é substituído a cada vez (o git guarda o histórico). Como o repositório é público, nada de segredos nem dados pessoais. O primeiro já está escrito.
>
> Tudo isso foi para o PR #28, que continua só com documentação.
>
> **Próximo passo:** a ADR-016 (formato do arquivo de projeto) e começar a construir o MVP (`flosub serve` + o app Svelte). Posso seguir?

### Reply 2 (2026-10-27): web editor first slice

> Feito. O editor já funciona de ponta a ponta: abrir → transcrever → editar → cortar → exportar.
>
> **Como testar**
> ```bash
> cd engine
> uv run flosub serve /caminho/do/video.mp4
> ```
> O navegador abre sozinho. O app já está compilado na sua máquina; se aparecer "The editor is not built", rode `cd web && npm ci && npm run build`.
>
> **ADR-016, o arquivo de projeto:** `video.mp4.legendaria.json`, ao lado do vídeo. É um JSON nosso, com versão e validação. Guarda os trechos mantidos (os cortes), as legendas no tempo do vídeo original e o estilo. `.ass`, SRT e VTT viram exportações. Isso fecha a sua pergunta antiga sobre `.ass` ou `.ass` estendido: outros editores, como o Aegisub, apagam seções desconhecidas ao salvar, e perderíamos os cortes e os tempos das palavras.
>
> **O que o editor faz**
> - Tela de transcrição: modelo, idioma, estilo e progresso.
> - Prévia exata ao vivo com o JASSUB: cada edição aparece no vídeo em menos de 1 s, com o mesmo libass da exportação.
> - Cortes: **I** marca o início, **O** marca o fim, **X** corta. A reprodução pula os trechos cortados. Na lista de cortes, "Restaurar" traz o trecho e as legendas de volta.
> - Lista de legendas: texto, tempos, dividir no cursor, juntar, apagar, adicionar.
> - Desfazer e refazer (Ctrl+Z / Ctrl+Shift+Z) e salvamento automático.
> - Exporta MP4 com a legenda gravada, SRT, VTT ou ASS, como `video.edited.*` ao lado do original.
> - Português e inglês. Os atalhos ficam num JSON editável.
>
> **Testes**
> - 120 testes do motor, incluindo um corte + gravação real com FFmpeg e as rotas do servidor.
> - 5 testes do app, um deles com 200 cortes aleatórios.
> - Um teste no navegador (Playwright): cortar, editar, desfazer, tocar pulando o corte, exportar. Também transcrevi o seu clipe de 20 s pelo servidor: 41 blocos.
>
> Três problemas apareceram e já foram corrigidos:
> - um corte menor que 10 ms deixava um buraco invisível;
> - a fonte não carregava no primeiro quadro;
> - com o vídeo pausado, a legenda não era redesenhada depois de um salto.
>
> **Ainda não tem:** forma de onda, arrastar blocos na timeline, encaixe (snap), zoom e as sugestões do glossário no editor. Essa é a próxima etapa. Por enquanto, a fonte da prévia só é encontrada automaticamente no Linux; nos outros sistemas o JASSUB usa uma fonte própria.
>
> **Recomendação de modelo:** a regra está no `AGENTS.md`, de forma neutra: nível **standard** (Sonnet e equivalentes) ou **top** (Opus e equivalentes), e esforço **low / medium / high**. Assim qualquer agente traduz para o próprio modelo. A recomendação também fica anotada no plano, para não se perder entre sessões.
>
> Tudo está no **PR #29** (https://github.com/flou-ainan/Legendaria/pull/29), que vem em cima do #28.
>
> **Next task:** o seu teste manual com `flosub serve`; depois, a timeline com forma de onda, arrastar e encaixe — tier: **standard** (Sonnet), effort: **medium** — o caminho já está definido pelos spikes e pelo plano 07.
