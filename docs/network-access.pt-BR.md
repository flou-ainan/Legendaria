# Usando o editor no celular (acesso pela rede)

[English](network-access.md) | **Português (Brasil)**

A Legendária roda no seu computador, e o celular pode ser uma segunda tela para ela. Este guia explica como isso funciona, por que pede uma senha e como usar no Wi-Fi de casa, pelo Tailscale ou pelo Headscale.

## Resumo

1. Abra o launcher (`legendaria`) e defina uma **senha de acesso** quando ele perguntar. Ou, no terminal: `flosub auth set`.
2. O launcher mostra um endereço como `http://192.168.1.20:8765/`. Abra no navegador do celular, no mesmo Wi-Fi.
3. Digite a senha uma vez. O celular continua conectado por 30 dias.

No próprio computador nada muda: o editor abre sem senha.

## Por que uma senha

Quem alcança o editor pode usá-lo, e o editor pode ler vídeos do seu computador. O Wi-Fi costuma ser compartilhado com visitas, e dar a uma visita acesso aos arquivos do computador principal da casa não é seguro. Por isso:

- **Sem senha, o editor só abre neste computador.** Nada escuta na rede.
- **Com senha, o editor também abre em outros aparelhos**, mas só para quem a conhece. Isso vale para o seu Wi-Fi, o Tailscale, o Headscale e os túneis: uma senha só para todos.
- **Mesmo conectado, o celular não navega nas pastas do computador.** Ele pode enviar um vídeo do próprio celular para editar e baixar o que exportou. Escolher arquivos do computador só é possível no computador.
- Senhas erradas são retardadas (depois de 5 erros a espera cresce, até 15 minutos), então não dá para adivinhar tentando muitas.
- Conexões de endereços públicos da internet são recusadas, mesmo com a senha certa. Se um dia você abrir uma porta no roteador por engano, isso impede que ela chegue ao editor.

A senha fica guardada só como um hash embaralhado, em um arquivo que só o seu usuário lê. Se esquecer, defina outra: nada se perde.

## O limite do Wi-Fi que você precisa saber

Na rede de casa o editor usa HTTP puro, então a senha e o login viajam sem criptografia. Isso afasta visitas curiosas, mas **quem consegue capturar o tráfego do mesmo Wi-Fi poderia ler a senha**. Para ficar mais seguro:

- Coloque as visitas no **Wi-Fi de convidados do roteador, com isolamento de clientes**, e deixe seus aparelhos na rede principal.
- Ou use **Tailscale / Headscale** (abaixo), que criptografam o tráfego e dão ao celular um endereço `https` seguro.

Use uma senha que você não usa em nenhum outro lugar. As geradas (`k7mq-x2vd-9tpr`) foram feitas para isso.

## Definir e trocar a senha

| O quê | Como |
|---|---|
| Definir na primeira vez | O launcher pergunta. Enquanto não houver senha, ele pergunta toda vez que você abre o editor; "Agora não" abre o editor só neste computador. |
| No terminal | `flosub auth set` (digitação oculta, ou Enter para gerar uma), ou `flosub auth set --generate` |
| Trocar | "Trocar a senha…" no launcher, Arquivo ▸ "Acesso e senha…" no editor, ou `flosub auth set` |
| Remover | `flosub auth reset` (o editor volta a abrir só neste computador) |
| Ver o estado e o arquivo | `flosub auth status` |

Trocar a senha desconecta todos os celulares.

## Mesmo Wi-Fi

1. Defina a senha e abra o editor pelo launcher (ou rode `flosub serve`).
2. Abra no celular o endereço que ele mostra.

Se o celular não conectar:

- O celular e o computador precisam estar na mesma rede, e não em uma rede de convidados com isolamento.
- **Firewall.** O Windows pergunta na primeira vez: permita em **redes privadas**. O macOS pede para aceitar conexões de entrada: permita. No Linux com `ufw`: `sudo ufw allow from 192.168.0.0/16 to any port 8765 proto tcp` (ajuste para a sua rede).
- A porta padrão é 8765. Se estiver ocupada, o launcher usa a próxima livre e mostra qual. No terminal: `flosub serve --port 8800`.

## Fora de casa: Tailscale

O [Tailscale](https://tailscale.com) cria uma rede privada e criptografada entre os seus aparelhos, sem configurar o roteador. O plano gratuito basta.

1. Instale o Tailscale no computador e no celular e entre na mesma conta.
2. No computador: `tailscale serve --bg 8765` (a porta que o editor usa). Ele mostra um nome como `https://meu-computador.nome-da-rede.ts.net`.
3. Inicie o editor liberando esse nome: `flosub serve --allow-host meu-computador.nome-da-rede.ts.net` (o nome sem o `https://`).
4. Abra esse endereço `https` no celular e digite a mesma senha.

No Linux, se o `tailscale serve` reclamar de permissão, rode uma vez: `sudo tailscale set --operator=$USER`.

**Não** use o `tailscale funnel`: ele publica o editor para a internet inteira. O `tailscale serve` fica dentro da sua rede privada.

## Por conta própria: Headscale

O [Headscale](https://headscale.net) é um servidor de código aberto que faz o papel do serviço de coordenação do Tailscale, em uma máquina que você mesmo mantém. Com os aparelhos conectados a ele, os passos são os mesmos do Tailscale: alcance o computador pelo nome ou pelo endereço `100.x.y.z`, inicie o editor com `--allow-host <esse nome>` quando usar um nome, e use a mesma senha. Montar um servidor Headscale está fora deste guia: veja a documentação dele.

## Ajustes que você pode editar

`flosub auth status` mostra o caminho do `access.json`. Além da senha embaralhada, ele tem chaves que você pode mudar em um editor de texto (reinicie o editor depois):

| Chave | Padrão | Significado |
|---|---|---|
| `lan` | `true` | Com senha, escutar na rede local. `false` mantém o editor só neste computador, qualquer que seja a senha. |
| `require_password_here` | `false` | `true` pede a senha também neste computador (um computador compartilhado). |
| `allow_public` | `false` | `true` aceita conexões de endereços públicos da internet. Não recomendado. |

## Nunca abra uma porta no roteador

Não redirecione uma porta da internet para o editor. Para usar fora de casa, use Tailscale ou Headscale: foram feitos para isso. Se uma porta ficar aberta mesmo assim, o editor recusa endereços públicos por padrão.

## Referência técnica

O desenho e o modelo de ameaças estão no [ADR-026](dev-docs/decisions/ADR-026-network-access-password-and-launcher.md) (em inglês).
