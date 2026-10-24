# Mapa do Projeto — Open Subtitler

> Resumo do projeto para agentes e pessoas acharem rápido o que precisam, sem reler o código.
> **Atualize este arquivo a cada mudança no projeto** (arquivos, funções, stack, estrutura). Convenções em `docs/dev-docs/README.md`.

**Última atualização:** 2026-10-23 — plano 01 e ADRs 001-003 (ainda sem código)

---

## 1. Visão geral

Gerador automático de legendas para vídeos, de código aberto, inspirado nas legendas automáticas do CapCut: transcreve o áudio, gera legendas sincronizadas (palavra a palavra), permite estilizar e exporta o vídeo com as legendas gravadas ou em arquivos SRT/VTT/ASS.

**Estado atual:** planejamento. MVP descrito em `dev-docs/planejamento/plano_01_mvp_transcricao_blender.md`. Nenhum código ainda.

## 2. Arquitetura

Duas partes independentes que conversam por arquivo JSON:

```
[vídeo na timeline do Blender]
        │  add-on chama via subprocess
        ▼
engine/ (opensub) ── faster-whisper na GPU ──► JSON v1 (segments + words)
        │                                       │  progresso: JSON por linha no stdout
        ▼                                       ▼
   SRT / VTT (CLI)            add-on cria text strips editáveis no VSE
                                         │
                                         ├──► Exportar SRT / VTT (a partir das strips)
                                         └──► Render do Blender com legendas gravadas
```

- **Motor (`engine/`):** pacote Python com venv próprio, comando `opensub`. Funciona sozinho pela linha de comando.
- **Add-on (`blender_addon/open_subtitler/`):** extensão do Blender 4.2+, com a UI na sidebar do sequencer.

## 3. Tecnologias / stack

| Camada | Tecnologia |
|---|---|
| Transcrição | faster-whisper 1.2 (CTranslate2 4.6), fp16 na GPU / int8 na CPU |
| Aceleração | CUDA 12 via `nvidia-cublas-cu12` + `nvidia-cudnn-cu12` 9 (pip), sem PyTorch |
| Áudio/vídeo | FFmpeg / PyAV |
| Editor | Blender 4.2 LTS, Video Sequence Editor (`bpy`) |
| Linguagem | Python 3.10+ (motor) / Python embutido do Blender (add-on) |
| Testes | pytest |
| Hardware de referência | RTX 2070 Super 8 GB, Linux Mint 22 |

## 4. Decisões técnicas

| ADR | Decisão | Status |
|---|---|---|
| [001](dev-docs/decisoes/ADR-001-faster-whisper.md) | faster-whisper como motor (Ollama não roda Whisper) | aceito |
| [002](dev-docs/decisoes/ADR-002-blender-vse-editor.md) | Blender VSE como editor interativo (text strips) | aceito |
| [003](dev-docs/decisoes/ADR-003-motor-processo-externo.md) | Motor como processo externo, contrato JSON | proposto |

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

- Plano 01 (MVP motor + add-on Blender) aguardando aprovação das questões em aberto.
- Estrutura alvo de pastas (`engine/`, `blender_addon/`) está no plano 01; entra na seção 5 quando for criada.
