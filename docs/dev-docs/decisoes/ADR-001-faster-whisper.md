# ADR 001 — faster-whisper como motor de transcrição

**Status:** aceito
**Data:** 2026-10-23

## Contexto

Precisamos transcrever áudio localmente, em português, com o tempo de cada palavra (base das legendas animadas estilo CapCut), usando a GPU da máquina (RTX 2070 Super, 8 GB).

## Decisão

Usar o **faster-whisper** (Whisper sobre CTranslate2), em fp16 na GPU, com fallback para CPU em int8.

## Alternativas consideradas

- **Ollama + Whisper da comunidade** (`dimavz/whisper-tiny`): descartado. O Ollama roda modelos GGUF de texto via llama.cpp e falha com `unknown model architecture`. Testado no brainstorm.
- **openai-whisper** (oficial): mais lento e usa mais VRAM, e depende de PyTorch.
- **WhisperX:** timestamps de palavra mais precisos (alinhamento forçado com wav2vec2), mas instalação mais pesada. Fica como possível melhoria se a precisão por palavra do faster-whisper não bastar.
- **whisper.cpp:** ideal para mobile/ARM. Fica para o plano mobile.

## Consequências

- Medido no brainstorm: 49 min de áudio em ~38 s com o modelo `base` na GPU.
- O CTranslate2 precisa do cuDNN 9 e do cuBLAS 12 visíveis para o linker. O motor resolve isso sozinho (ver plano 01).
- Não é preciso PyTorch.
