# ADR 002 — Blender VSE como editor interativo das legendas

**Status:** aceito
**Data:** 2026-10-23

## Contexto

O objetivo é uma experiência parecida com a do CapCut: gerar as legendas automaticamente e depois **editar de forma interativa**, corrigindo texto, ajustando tempo e estilizando, além de exportar arquivos de legenda.

## Decisão

Construir um **add-on (extensão) do Blender** para o Video Sequence Editor. Cada legenda vira uma text strip nativa na timeline. A exportação SRT/VTT é feita a partir das strips, sem depender da renderização.

## Alternativas consideradas

- **Gerar `.ass` e gravar com FFmpeg:** suporta estilos e karaokê, mas não tem edição interativa. Pode virar um formato extra de exportação.
- **Kdenlive:** maduro e com speech-to-text próprio, mas a extensão é feita por scripts externos e pela edição do XML do MLT, sem uma API de UI rica.
- **OpenShot:** interface em Python, mas o motor de texto é limitado.
- **Editor próprio:** trabalho demais para o MVP.

## Consequências

- A UI, a timeline, o preview e a renderização vêm prontos do Blender.
- O Python embutido do Blender não tem as dependências do motor, daí o ADR-003.
- A API do VSE muda entre versões (`sequences` → `strips` a partir do 4.4), então o acesso fica isolado em uma camada de compatibilidade.
- Licença: a plataforma oficial de extensões exige GPL-3.0-or-later (questão aberta no plano 01).
