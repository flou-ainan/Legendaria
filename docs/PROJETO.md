# Mapa do Projeto — Open Subtitler

> Resumo do projeto para agentes e pessoas acharem rápido o que precisam, sem reler o código.
> **Atualize este arquivo a cada mudança no projeto** (arquivos, funções, stack, estrutura). Convenções em `docs/dev-docs/README.md`.

**Última atualização:** 2026-10-23 — passo 00 (setup do repositório)

---

## 1. Visão geral

Gerador automático de legendas para vídeos, de código aberto, inspirado nas legendas automáticas do CapCut: transcreve o áudio, gera legendas sincronizadas (palavra a palavra), permite estilizar e exporta o vídeo com as legendas gravadas ou em arquivos SRT/VTT/ASS.

**Estado atual:** só a estrutura do repositório e a documentação. Nenhum código ainda.

## 2. Arquitetura

_A definir._ Será registrada aqui e em `docs/dev-docs/decisoes/` quando for escolhida.

## 3. Tecnologias / stack

_A definir._

## 4. Decisões técnicas

| ADR | Decisão | Status |
|---|---|---|
| — | Nenhuma ainda | — |

## 5. Estrutura de pastas

```
Open-Subtitler/
├── AGENTS.md              # instruções para qualquer agente de IA
├── CLAUDE.md              # aponta para AGENTS.md
├── README.md              # apresentação pública do projeto
├── LICENSE                # MIT
├── .gitignore
└── docs/
    ├── PROJETO.md         # este arquivo
    └── dev-docs/
        ├── README.md      # convenções de documentação
        ├── planejamento/  # planos (antes de implementar)
        ├── devlog/        # passos executados
        └── decisoes/      # ADRs
```

## 6. Mapa de arquivos

Ainda não há arquivos de código. Quando houver, cada arquivo entra aqui assim:

```markdown
### caminho/arquivo.py — N linhas
Descrição curta do papel do arquivo.

| Função / classe | Linha | O que faz |
|---|---|---|
| `nome_funcao(args)` | 12 | ... |
```

## 7. Em andamento

- Definir a stack e a arquitetura (próximo passo).
