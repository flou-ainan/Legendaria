# ADR 003 — Motor como processo externo, conversando por JSON

**Status:** proposto
**Data:** 2026-10-23

## Contexto

O Blender traz seu próprio Python. Instalar faster-whisper, CTranslate2 e as bibliotecas CUDA dentro dele é frágil e quebra a cada atualização do Blender.

## Decisão

O motor (`engine/`) é um pacote Python independente, com venv próprio e o comando `opensub`. O add-on o executa com `subprocess.Popen`:

- O progresso chega como JSON por linha no stdout.
- O resultado é um arquivo JSON versionado, com segmentos e palavras com tempos.

## Alternativas consideradas

- **Instalar as dependências no Python do Blender:** frágil, e um erro de cuDNN derrubaria o Blender inteiro.
- **Servidor HTTP local:** útil no futuro (mobile/nuvem), mas complexo demais para o MVP.

## Consequências

- O motor também funciona sozinho pela linha de comando e pode ser reaproveitado por uma API no futuro.
- Se o motor quebrar, ele não derruba o Blender.
- O formato JSON vira um contrato e precisa de versão (`"version": 1`).
- A formatação de timestamps fica duplicada em dois lugares (motor e add-on), porque o add-on não importa o motor.
