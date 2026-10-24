# Instruções para agentes

Vale para qualquer agente (Claude Code, Gemini/Antigravity, OpenCode, Copilot, Codex...).

## Antes de começar

1. Leia `docs/PROJETO.md`: visão geral, stack, decisões e mapa de arquivos com linhas e funções.
2. Leia o último passo em `docs/dev-docs/devlog/` e os planos abertos em `docs/dev-docs/planejamento/` para saber o que está em andamento.
3. Só então abra os arquivos de código ligados à tarefa. Não varra o repositório inteiro se a documentação já responde.

## Regras de documentação (obrigatórias)

As convenções completas estão em `docs/dev-docs/README.md`. Resumo:

- **Todo planejamento vira arquivo** em `docs/dev-docs/planejamento/` antes da implementação.
- **Toda alteração é registrada** em um passo do devlog em `docs/dev-docs/devlog/`: o que mudou, por quê, arquivos tocados e como foi testado.
- **Toda decisão técnica relevante** (escolha de biblioteca, arquitetura, formato) vira um ADR em `docs/dev-docs/decisoes/`.
- **`docs/PROJETO.md` reflete sempre o estado atual do código.** Qualquer mudança em arquivos, funções, stack ou estrutura de pastas atualiza o `PROJETO.md` no mesmo commit, incluindo a contagem de linhas.

A ideia: alguém que clone o repositório, sem acesso a nenhuma memória de agente, consegue entender o projeto e o que está acontecendo só lendo `docs/`.

## Memória entre agentes

Esta máquina usa o [ai-memory](https://github.com/akitaonrails/ai-memory) para passar contexto entre agentes. Ele é um complemento: a fonte oficial do estado do projeto é sempre `docs/`.

## Geral

- Não commite segredos, chaves de API ou arquivos de mídia de teste.
- Preserve alterações locais que não são suas.
- Ao terminar, informe o que foi validado.
