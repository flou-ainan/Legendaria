# Passo 01 — Plano do MVP a partir do brainstorm

**Data:** 2026-10-23
**Agente/autor:** Claude Code (Opus 5.5), com flou-ainan
**Plano relacionado:** planejamento/plano_01_mvp_transcricao_blender.md

## O que foi feito

- Lido o brainstorm com o Gemini (`docs/whisper-blender-brainstorm.md`). A parte mobile foi ignorada, como pedido.
- Escrito o plano 01: motor `opensub` (faster-whisper → JSON com palavras) + add-on do Blender (text strips editáveis, exportação SRT/VTT).
- Registradas as decisões: ADR-001 (faster-whisper), ADR-002 (Blender VSE), ADR-003 (motor como processo externo).
- `PROJETO.md` atualizado com arquitetura, stack e decisões.
- Ambiente conferido: Blender 4.2.0, Python 3.10.12, faster-whisper 1.2.1, ctranslate2 4.6.1, cuDNN 9.1 e cuBLAS 12.1 (pip), ffmpeg 4.4.2, RTX 2070 Super 8 GB.

## Por quê

Transformar a conversa exploratória em um plano executável, corrigindo os problemas do código de exemplo do Gemini (lista no plano 01).

## Arquivos tocados

- `docs/dev-docs/planejamento/plano_01_mvp_transcricao_blender.md` (novo)
- `docs/dev-docs/decisoes/ADR-001-*.md`, `ADR-002-*.md`, `ADR-003-*.md` (novos)
- `docs/PROJETO.md`, este arquivo

## Como foi testado

Só documentação; nada para executar.

## Pendências / próximos passos

- Responder as questões em aberto do plano 01.
- Decidir se o brainstorm vai para o git: ele contém caminhos e nomes de arquivos de clientes, e o repositório é público.
- Após a aprovação: etapa 1 (motor).
