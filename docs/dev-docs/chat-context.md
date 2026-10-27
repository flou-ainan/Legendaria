# Chat context (hand-off)

**Last updated:** 2026-10-27, by Claude Code (Opus 5.5), during step 30.
**Policy:** `AGENTS.md` and `docs/dev-docs/README.md` ("chat-context.md"). This is a snapshot that gets replaced, never appended. It is public: no secrets and no private data.

## Summary of the conversation so far

**Who and how**
- The owner (GitHub `flou-ainan`) chats in Brazilian Portuguese, so agents reply in Portuguese.
- Dev docs and code are in English. User-facing text is in en + pt-BR.
- The owner tests manually and then gives feedback. They prefer lean MVPs with "later" notes, and want options plus a recommendation before a decision.
- They avoid heavy frameworks and libraries.
- Public actions need explicit approval every time: PyPI tags, releases, and anything published.
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

**Open and next**
- **Next:**
  - ADR-016: the project file `<video>.legendaria.json` (`"format": "legendaria-project"`, version 1, JSON Schema, kept ranges + cues + style; cues in source time);
  - then the plan 07 phase 2 MVP build: `flosub serve`, the Svelte app in `web/`, the JASSUB player, the cue list, the timeline (cuts + cues + waveform), export, pt-BR.
- **Pending owner decisions:** import `.ass`/`.srt` + `flosub align --srt` (plan 04 §11.3, item 4).
- **Not published:** engine 0.1.0.dev4 is not on PyPI; the tag needs the owner's approval.
- **Open PR:** #28 (the docs for steps 28–30).

## Last two complete replies (verbatim)

### Reply 1 (2026-10-26): phase 0 results

> Os quatro testes rodaram e funcionaram. Para o framework, recomendo **Svelte 5**, com o Vue 3 bem perto; a escolha é sua.
>
> Tudo está em **`/mnt/work/Trabalhos/Projetos Flou/legendaria-spikes/`**, com um `LEIA-ME.md` explicando cada arquivo. A pasta fica fora do repositório porque usa o seu vídeo. O servidor dos testes está rodando agora em **http://localhost:5199**, então dá para abrir direto no navegador.
>
> ### 1.1 OpenReel: aproveitamos as ideias, não o código
> - São cerca de 460 mil linhas. Ele monta cada quadro em canvas porque mistura várias faixas e efeitos.
> - Nós temos um vídeo só. Um `<video>` comum com a legenda do JASSUB por cima resolve.
> - O motor dele, a forma de onda e a exportação são substituídos por coisas mais simples.
> - Vale estudar como ele encaixa os blocos na timeline, o desfazer e os atalhos. Copiar o React dele traz pouco ganho.
>
> ### 1.2 JASSUB, a prévia exata (`results/1.2-jassub/`)
> - Comparei quadro a quadro com o FFmpeg, inclusive no meio da animação "pop".
> - Sobram só diferenças de 1 pixel nas bordas: nos arquivos `side_*.png` a linha de baixo (a diferença) fica quase preta.
> - Abre em 0,2 a 0,5 s.
> - **O que precisa:** o servidor tem que entregar as fontes ao navegador, senão ele não enxerga as fontes do sistema. E o primeiro quadro só aparece depois que a fonte carrega.
>
> ### 1.3 Forma de onda com 500 blocos (`results/1.3-wavesurfer/`)
>
> | Caso | Abre em | Memória |
> |---|---|---|
> | Clipe de 20 s, 43 blocos | 35 ms | 2 MB |
> | 10 min, 500 blocos, navegador decodifica o áudio | 1,2 s | 27 MB |
> | 10 min, 500 blocos, **picos calculados no servidor** | **53 ms** | **9 MB** |
>
> - Arrastar as bordas e dividir um bloco funcionam.
> - **Decisão que sai daqui:** os picos da forma de onda vêm do servidor. Calcular 10 min leva 1,2 s.
> - No modo de 10 min, o teste automático de arrastar não valeu, porque a tela rolou e o bloco saiu de vista. Por isso o arraste só foi conferido no clipe de 20 s.
>
> ### 1.4 Cortar e gravar a legenda num comando só (`results/1.4-cut-burn/`)
> - Tirei os trechos de 4–7 s e 12,5–15 s. Saiu exatamente 14,5 s, renderizado em 8 s.
> - Dos 43 blocos sobraram 31, e o SRT e o VTT já saem no tempo novo.
> - O `sync_check.png` mostra o original e o cortado no mesmo instante da fala. A legenda e a boca batem.
> - Os 4 testes automáticos do ajuste de tempos passaram.
>
> ### 2.1 Framework
> O que pesa no editor (o vídeo, a legenda do JASSUB e a forma de onda) já funciona sem framework nenhum. O framework só cuida da lista de blocos, dos cortes, da seleção e do desfazer. A regra que vale em qualquer um: **o tempo do player não passa pelo estado a 60 quadros por segundo**. O que causa travamentos no React em projetos grandes é justamente o estado mudando a cada quadro.
>
> - **Svelte 5 (recomendo):** é o mais leve. Os componentes ficam muito próximos de HTML/JS puro, o que combina com o seu jeito de evitar frameworks. A reatividade é precisa: atualiza só o que mudou.
> - **Vue 3:** fica bem perto. É maduro e fácil para colaboradores.
> - **React:** você conhece, mas não ganhamos nada copiando o OpenReel.
>
> ### 2.2 MVP enxuto
> Os cortes no MVP só removem trechos. Anotei no plano 07, na seção "Later", o que fica para depois:
> - reordenar trechos e juntar vários vídeos;
> - ajustes automáticos de tempo no estilo do Aegisub;
> - timeline em canvas para milhares de blocos;
> - uma versão para celular sem servidor (por enquanto o servidor local está sempre presente);
> - escolha de fontes.
>
> A nota técnica completa e o devlog (passo 29) foram para o **PR #28** (https://github.com/flou-ainan/Legendaria/pull/28), que segue aberto e só tem documentação.
>
> **Svelte 5 ou Vue 3?** Com a sua escolha eu escrevo a ADR-015 e começo a fase 1.

### Reply 2 (2026-10-27): Svelte chosen, OpenReel dissected, hand-off policy

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
