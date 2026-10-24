# Passo 00 — Setup do repositório e da documentação

**Data:** 2026-10-23
**Agente/autor:** Claude Code (Opus 5.5), com flou-ainan

## O que foi feito

1. Repositório git criado na branch `main` com `README.md`, `.gitignore` (Python, Node, `.env`, arquivos de mídia) e `LICENSE` (MIT).
2. Repositório público criado no GitHub: https://github.com/flou-ainan/Open-Subtitler
3. Estrutura de documentação criada: `AGENTS.md`, `CLAUDE.md`, `docs/PROJETO.md` e `docs/dev-docs/` com `planejamento/`, `devlog/` e `decisoes/`.
4. [ai-memory](https://github.com/akitaonrails/ai-memory) v3.2.2 instalado na máquina de desenvolvimento, ligado ao Claude Code, OpenCode, Antigravity CLI e Copilot CLI.

## Por quê

O projeto vai ser desenvolvido alternando entre agentes diferentes. Há uma contingência dupla:

- **ai-memory:** memória automática entre agentes e sessões, local na máquina.
- **`docs/` no git:** planos, devlog, ADRs e `PROJETO.md`. Funciona sem nenhuma ferramenta e para qualquer pessoa que clone o repositório.

O padrão de documentação segue o que já é usado em outros projetos do autor (`mercados`, `action_app_bundle`, `holding_python`).

## Arquivos tocados

- `README.md`, `.gitignore`, `LICENSE`, `AGENTS.md`, `CLAUDE.md`
- `docs/PROJETO.md`, `docs/dev-docs/README.md`, este arquivo

## Como foi testado

- `git push` para `origin/main` funcionou.
- `ai-memory setup` concluiu com `healthz: ok` e `memory_status: ok`.

## Pendências / próximos passos

- Reiniciar os agentes para carregarem os ganchos do ai-memory.
- Definir stack e arquitetura a partir da conversa inicial com o Gemini → plano 01 e primeiros ADRs.
