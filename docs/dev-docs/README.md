# Convenções de documentação de desenvolvimento

Toda a história do projeto fica em markdown dentro do repositório. Isso funciona como contingência: mesmo sem o ai-memory ou qualquer memória de agente, quem pegar o projeto no git entende o que existe, o que foi feito e o que está em andamento.

## Estrutura

```
docs/
├── PROJETO.md              # mapa do projeto, sempre atualizado
└── dev-docs/
    ├── README.md           # este arquivo
    ├── planejamento/       # planos, escritos antes de implementar
    ├── devlog/             # um passo por alteração ou etapa executada
    └── decisoes/           # ADRs: decisões técnicas e seus motivos
```

## `docs/PROJETO.md`

Arquivo resumido para agentes e pessoas acharem rápido o que precisam, sem reler o código. Contém:

1. Visão geral do projeto
2. Arquitetura escolhida
3. Tecnologias / stack
4. Decisões técnicas (resumo com link para o ADR)
5. Estrutura de pastas
6. Mapa de arquivos: para cada arquivo de código, a quantidade de linhas e uma descrição básica de cada função ou classe, com a linha onde começa

**Regra:** toda mudança no projeto atualiza o `PROJETO.md` no mesmo commit. Linhas podem ser contadas com `wc -l`.

## Planejamento — `planejamento/plano_NN_<tema>.md`

Escrito **antes** de implementar. Numeração sequencial (`plano_01_transcricao.md`).

```markdown
# Plano NN — <tema>

**Status:** proposto | aprovado | em execução | concluído | abandonado
**Data:** AAAA-MM-DD

## Objetivo
## Contexto
## Mudanças propostas   (arquivos a criar/alterar e o que muda em cada um)
## Questões em aberto
## Critérios de pronto / como testar
```

Quando o status mudar, atualize o arquivo.

## Devlog — `devlog/passo_NN_<tema>.md`

Um arquivo por alteração ou etapa executada, numeração sequencial (`passo_01_transcricao_whisper.md`). Registra o que **foi feito**, não o que se pretende fazer.

```markdown
# Passo NN — <tema>

**Data:** AAAA-MM-DD
**Agente/autor:** <quem fez>
**Plano relacionado:** planejamento/plano_NN_<tema>.md (se houver)
**Commit(s):** <hash>

## O que foi feito
## Por quê
## Arquivos tocados
## Como foi testado
## Pendências / próximos passos
```

## Decisões técnicas — `decisoes/ADR-NNN-<tema>.md`

Para escolhas que alguém pode questionar depois: biblioteca, arquitetura, formato de arquivo, troca de abordagem.

```markdown
# ADR NNN — <título>

**Status:** proposto | aceito | substituído por ADR-XXX
**Data:** AAAA-MM-DD

## Contexto
## Decisão
## Alternativas consideradas
## Consequências
```

Ao criar um ADR, adicione uma linha na seção "Decisões técnicas" do `PROJETO.md`.

## Fluxo de uma mudança

1. Planejar → `planejamento/plano_NN_*.md`
2. Se houver decisão técnica → `decisoes/ADR-NNN-*.md`
3. Implementar
4. Registrar → `devlog/passo_NN_*.md`
5. Atualizar `PROJETO.md`
6. Commit com código e documentação juntos
