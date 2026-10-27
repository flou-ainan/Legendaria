<p align="center">
  <img alt="Legendária — legendas livres, estilo CapCut" src="assets/brand/banner-pt-BR.svg" width="760">
</p>

# Legendária

[English](README.md) | **Português (Brasil)**

**Legendas livres, estilo CapCut.** Legendas automáticas gratuitas e de código aberto para os seus vídeos, inspiradas nas legendas automáticas do CapCut.

O nome junta *legenda* com *legendary* (lendária, em inglês). A ferramenta de linha de comando se chama `flosub`.

> 🚧 Em desenvolvimento inicial. Ainda não há nada para instalar.

## O que ele vai fazer

- **Transcrever automaticamente**, no seu próprio computador (acelerado pela placa de vídeo quando houver, ou pelo processador). Sem nuvem, sem conta, sem coleta de dados.
- **Editar visualmente no navegador:** um editor local que abre no seu navegador (nada é enviado para a internet). Cada legenda é um bloco na linha do tempo: clique para corrigir o texto, arraste para ajustar o tempo, corte as partes do vídeo que não quer e veja o visual final ao vivo.
- **Exportar** SRT, VTT ou ASS para o YouTube e outras plataformas, ou o vídeo com as legendas gravadas.
- **Legendas animadas palavra por palavra** (estilo CapCut), depois da primeira versão.

## Objetivos

- Instalador simples: avançar → avançar → concluir, abrir o editor no navegador, colocar o vídeo, clicar em **Gerar legendas** e editar.
- Funciona em **Linux, macOS e Windows 10+**.
- Disponível em **inglês e português do Brasil**. Outros idiomas são bem-vindos.
- **Personalizável:** padrões, modelos, estilos e traduções ficam em arquivos JSON que você pode editar.

## Status e próximos passos

O motor de transcrição já funciona pela linha de comando (`flosub`). O editor no navegador está sendo construído ([plano 07](docs/dev-docs/planning/plan_07_web_editor.md), documentação técnica em inglês). Um add-on anterior para o Blender está congelado e deve ser aposentado ([ADR-014](docs/dev-docs/decisions/ADR-014-web-editor-blender-frozen.md)). Um site de documentação e um vídeo tutorial virão com a primeira versão.

## Como contribuir

Contribuições são bem-vindas, inclusive traduções. Leia o [CONTRIBUTING.md](CONTRIBUTING.md) (em inglês) e depois o [AGENTS.md](AGENTS.md) e o [docs/PROJECT.md](docs/PROJECT.md): juntos, eles explicam a estrutura, as convenções e o trabalho em andamento.

## Licença

- Motor de transcrição e repositório: [MIT](LICENSE)
- Add-on do Blender (congelado): GPL-3.0-or-later (exigência da plataforma de extensões do Blender)
