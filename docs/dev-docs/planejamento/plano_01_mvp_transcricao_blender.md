# Plano 01 — MVP: motor de transcrição + add-on do Blender

**Status:** proposto
**Data:** 2026-10-23
**Origem:** brainstorm com o Gemini em `docs/whisper-blender-brainstorm.md`
**Decisões ligadas:** ADR-001, ADR-002, ADR-003

## Objetivo

Ter o fluxo completo funcionando no desktop (Linux Mint, RTX 2070 Super):

1. Importar um vídeo no Blender (VSE).
2. Clicar em **Gerar legendas**: o áudio é transcrito na GPU com faster-whisper.
3. As legendas aparecem como **text strips editáveis** na timeline: corrigir texto, arrastar tempos, mudar estilo.
4. Exportar **SRT/VTT** a partir das strips, sem renderizar, ou renderizar o vídeo com as legendas gravadas.

**Fora de escopo neste plano:** app mobile (whisper.cpp / React Native) e API na nuvem. Ficam para um plano futuro.

## Contexto

O que o brainstorm já validou na prática:

- **Ollama não roda Whisper.** Os modelos da comunidade falham com `unknown model architecture` (ADR-001).
- **faster-whisper na GPU funciona.** 49 min de áudio em ~38 s com o modelo `base`, em fp16.
- **cuDNN:** o CTranslate2 precisa de `libcudnn_ops.so.9`, instalada pelo pip em `site-packages/nvidia/cudnn/lib`. Sem `LD_LIBRARY_PATH` apontando para lá, o processo aborta com core dump.
- **`.ass` não serve como editor:** não dá para editar de forma interativa. O Blender VSE dá edição visual e scripts em Python (ADR-002).
- **O Python embutido do Blender não tem faster-whisper nem CUDA.** O add-on chama o motor como processo externo e troca dados por JSON (ADR-003).

Ambiente verificado em 2026-10-23: Blender 4.2.0, Python 3.10.12, faster-whisper 1.2.1, ctranslate2 4.6.1, nvidia-cudnn-cu12 9.1, nvidia-cublas-cu12 12.1, ffmpeg 4.4.2, driver NVIDIA 595.

### Pontos do código do brainstorm que serão corrigidos

| Problema no código do Gemini | Como fica |
|---|---|
| O JSON só guarda os segmentos e descarta as palavras | O JSON guarda `words` com o tempo de cada palavra, base do estilo CapCut |
| `subprocess.run` congela o Blender durante a transcrição | Operador modal com timer: lê o progresso do processo sem travar a UI |
| Caminhos fixos (`/home/flou/...`, `python3.10`) no código | Caminho do motor configurável nas preferências do add-on; o motor acha o cuDNN sozinho |
| `LD_LIBRARY_PATH` no `.bashrc` | O próprio motor localiza as libs da NVIDIA no seu ambiente e as carrega antes do CTranslate2 |
| PyTorch instalado só para obter o cuDNN | Não é necessário: o faster-whisper não usa torch. Bastam `nvidia-cublas-cu12` e `nvidia-cudnn-cu12` |
| Exportação usa `frame_start`/`frame_end` | Usa `frame_final_start`/`frame_final_end`, que respeitam cortes na strip |
| `int()` na conversão para frames | `round()`, para não acumular deslocamento |
| Formatação de timestamp com `str(timedelta)` | Função própria testada, com horas acima de 24 e milissegundos corretos |

## Mudanças propostas

### Estrutura de pastas alvo

```
engine/                         # motor de transcrição (Python comum, venv próprio)
├── pyproject.toml              # pacote "opensub-engine", comando `opensub`
├── opensub_engine/
│   ├── __init__.py
│   ├── cli.py                  # argparse: transcribe / export
│   ├── cuda_libs.py            # localiza e pré-carrega cuDNN/cuBLAS do venv
│   ├── transcriber.py          # faster-whisper: GPU com fallback para CPU, progresso
│   ├── schema.py               # formato do JSON (segments + words), versão
│   └── formats.py              # JSON → SRT / VTT
└── tests/
    ├── test_formats.py
    └── test_schema.py

blender_addon/open_subtitler/   # extensão do Blender 4.2+
├── blender_manifest.toml
├── __init__.py                 # register/unregister
├── preferences.py              # caminho do motor, modelo, idioma, device
├── properties.py               # props da cena: canal, estilo padrão
├── operators.py                # transcrever (modal), exportar SRT/VTT
├── strips.py                   # JSON → text strips; strips → lista de legendas
├── compat.py                   # diferenças da API do VSE entre versões do Blender
└── panel.py                    # aba "Legendas" na sidebar do sequencer
```

### Etapa 1 — Motor de transcrição (`engine/`)

- **[NOVO]** `engine/pyproject.toml`, com dependências `faster-whisper`, `nvidia-cublas-cu12` e `nvidia-cudnn-cu12==9.*`. Venv em `engine/.venv`, já coberto pelo `.gitignore`.
- **[NOVO]** `cuda_libs.py`: encontra `nvidia/cudnn/lib` e `nvidia/cublas/lib` dentro do venv e carrega as `.so` com `ctypes` antes de importar o `ctranslate2`. Se não der certo, o processo reinicia a si mesmo com o `LD_LIBRARY_PATH` certo. Assim não é preciso mexer no `.bashrc`.
- **[NOVO]** `transcriber.py`:
  - `WhisperModel` com `device="cuda"` e `compute_type="float16"`. Se a GPU falhar, cai para `cpu`/`int8` e avisa.
  - `word_timestamps=True` e `vad_filter=True`, que corta silêncios e reduz frases inventadas pelo modelo.
  - O idioma pode ser fixado (`--language pt`) ou detectado automaticamente.
  - O progresso sai em **JSON por linha no stdout**, por exemplo `{"event":"progress","t":123.4,"total":2968}`, para o Blender ler. No terminal, aparece a barra do tqdm.
  - O ffmpeg extrai o áudio quando a entrada é vídeo (o próprio faster-whisper aceita vídeo via PyAV; confirmar na implementação).
- **[NOVO]** `schema.py`, com o formato do JSON v1:
  ```json
  {
    "version": 1,
    "source": "video.mp4",
    "language": "pt", "language_probability": 0.99,
    "duration": 2968.4, "model": "small",
    "segments": [
      {"start": 0.0, "end": 2.5, "text": "Olá, este é um teste.",
       "words": [{"start": 0.0, "end": 0.4, "word": "Olá,", "probability": 0.98}]}
    ]
  }
  ```
- **[NOVO]** `formats.py`: JSON → SRT e JSON → VTT.
- **[NOVO]** `cli.py`:
  - `opensub transcribe <arquivo> [--model small] [--language pt] [--device auto|cuda|cpu] [--output-dir .] [--format json,srt,vtt]`
  - `opensub export <arquivo.json> --format srt|vtt`
- **Testes:** formatação de timestamps (0 s, 59,999 s, > 1 h, > 24 h), SRT e VTT válidos, leitura e escrita do schema. A transcrição real é testada à mão com um vídeo curto.

### Etapa 2 — Add-on do Blender (`blender_addon/open_subtitler/`)

- Formato de **extensão do Blender 4.2** (`blender_manifest.toml`), instalável por zip.
- **Preferências:** caminho do executável `opensub` (ou do Python do venv do motor), modelo, idioma e device.
- **Operador "Gerar legendas"** (modal):
  1. Pega a strip ativa (`MOVIE` ou `SOUND`) e resolve o caminho com `bpy.path.abspath`.
  2. Inicia `opensub transcribe ... --format json` com `subprocess.Popen`.
  3. Um timer lê o stdout e atualiza a barra de progresso do Blender (`window_manager.progress_update`) e o texto de status. `Esc` cancela e mata o processo.
  4. Ao terminar, lê o JSON e cria uma text strip por segmento no canal escolhido. A posição leva em conta o início da strip de mídia e cortes no começo (`frame_offset_start`).
- **Operador "Exportar SRT/VTT":**
  - Lê as text strips do canal, ordenadas por `frame_final_start`, converte frames em segundos com o fps real (`fps / fps_base`) e grava ao lado do `.blend`.
  - A formatação de timestamp é a mesma do motor. O código fica copiado em `strips.py`, porque o add-on não pode importar o motor.
- **`compat.py`:** no Blender 4.4+, `sequence_editor.sequences` vira `strips` (a API antiga é removida no 5.0). O acesso fica isolado em um só lugar.
- **Painel** "Legendas" na sidebar do sequencer: configuração, gerar, exportar.

### Etapa 3 — Estilo CapCut (próximo plano, só registrado aqui)

- Quebrar os segmentos em blocos curtos (máximo de N palavras ou caracteres por linha) usando os tempos de cada palavra.
- Destaque da palavra atual (karaokê), com strips por palavra ou por grupo e uma cor de destaque.
- Presets de estilo: fonte, contorno, sombra, caixa de fundo, posição.
- Renderização com as legendas gravadas pelo próprio Blender.

## Questões em aberto

1. **Ambiente do motor:** um venv próprio em `engine/.venv` (recomendado: isolado, reproduzível e sem caminho `python3.10` fixo) ou reaproveitar o faster-whisper que já está em `~/.local`?
2. **Modelo padrão:** `small` (rápido), `medium` ou `large-v3-turbo`? Os dois últimos cabem nos 8 GB em fp16 e erram menos em termos técnicos em português. Sugestão: padrão `small`, configurável.
3. **Licença do add-on:** a plataforma de extensões do Blender exige GPL-3.0-or-later, e o repositório é MIT. Opções: deixar a pasta `blender_addon/` em GPL-3.0 e o motor em MIT, ou não publicar na plataforma oficial.
4. **Blender alvo:** 4.2 LTS, que é o instalado, com `compat.py` cobrindo 4.4+/5.x. Ok?
5. **Brainstorm:** mover `docs/whisper-blender-brainstorm.md` para `docs/dev-docs/referencias/`?

## Critérios de pronto

- [ ] `opensub transcribe video.mp4` gera JSON, SRT e VTT, usando a GPU sem nenhum `export` manual.
- [ ] Sem GPU, ou com `--device cpu`, a transcrição funciona em modo CPU.
- [ ] Os testes do motor passam (`pytest engine/tests`).
- [ ] No Blender 4.2: selecionar um vídeo → Gerar legendas → strips aparecem no canal certo, alinhadas ao áudio, com a barra de progresso andando e a UI sem travar.
- [ ] Editar texto e tempo de uma strip → Exportar SRT → o arquivo reflete a edição.
- [ ] `PROJETO.md` atualizado com todos os arquivos, linhas e funções; um devlog por etapa.
