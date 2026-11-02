# Using the editor from your phone (network access)

**English** | [Português (Brasil)](network-access.pt-BR.md)

Legendária runs on your computer, and your phone can be a second screen for it. This guide explains how that works, why it asks for a password, and how to use it on your home Wi-Fi, through Tailscale or through Headscale.

## In short

1. Open the launcher (`legendaria`) and set an **access password** when it asks. Or in a terminal: `flosub auth set`.
2. The launcher shows an address like `http://192.168.1.20:8765/`. Open it in your phone's browser, on the same Wi-Fi.
3. Type the password once. The phone keeps you signed in for 30 days.

On the computer itself nothing changes: the editor opens without a password.

## Why a password

Anyone who can reach the editor can use it, and the editor can read videos on your computer. A Wi-Fi network is often shared with visitors, and giving a visitor access to the files of your main computer is not safe. So:

- **Without a password, the editor can only be opened on this computer.** Nothing listens on the network.
- **With a password, the editor is also reachable from other devices**, but only for someone who knows it. This applies to your Wi-Fi, to Tailscale, to Headscale and to tunnels alike: one password for all of them.
- **Even signed in, a phone cannot browse your computer's folders.** It can send a video from the phone to be edited and download what it exports. Choosing files on the computer is only possible on the computer.
- Wrong guesses are slowed down (after 5 mistakes the wait grows, up to 15 minutes), so the password cannot be guessed by trying many.
- Connections from public internet addresses are refused, even with the right password. If you ever open a port on your router by mistake, this stops it from reaching the editor.

The password is stored only as a scrambled hash, in a file only your user can read. If you forget it, set a new one: nothing is lost.

## The local network (Wi-Fi) limit you should know

On your home network the editor speaks plain HTTP, so the password and the sign-in travel without encryption. That keeps curious visitors out, but **someone who can capture the traffic of the same Wi-Fi could read the password**. To be safer:

- Put visitors on the router's **guest Wi-Fi with client isolation**, and keep your own devices on the main network.
- Or use **Tailscale / Headscale** (below), which encrypts the traffic and gives the phone a secure `https` address.

Use a password you do not use anywhere else. The generated ones (`k7mq-x2vd-9tpr`) are made for this.

## Setting and changing the password

| What | How |
|---|---|
| Set it the first time | The launcher asks. Until one is set, it asks every time you open the editor; "Not now" opens the editor on this computer only. |
| In a terminal | `flosub auth set` (hidden typing, or press Enter to generate one), or `flosub auth set --generate` |
| Change it | The launcher's "Change the password…", the editor's File ▸ "Access and password…", or `flosub auth set` |
| Remove it | `flosub auth reset` (the editor goes back to this computer only) |
| See the state and the file | `flosub auth status` |

Changing the password signs every phone out.

## Same Wi-Fi

1. Set the password and open the editor from the launcher (or run `flosub serve`).
2. Open the address it shows on your phone.

If the phone cannot connect:

- The phone and the computer must be on the same network, and not on a guest network with isolation.
- **Firewall.** Windows asks the first time: allow **private networks**. macOS asks to accept incoming connections: allow. On Linux with `ufw`: `sudo ufw allow from 192.168.0.0/16 to any port 8765 proto tcp` (adjust to your network).
- The default port is 8765. If it is busy the launcher uses the next free one, and shows it. With the terminal: `flosub serve --port 8800`.

## Away from home: Tailscale

[Tailscale](https://tailscale.com) makes a private, encrypted network between your devices, with no router setup. The free plan is enough.

1. Install Tailscale on the computer and on the phone and sign in to the same account.
2. On the computer: `tailscale serve --bg 8765` (the port the editor uses). It prints a name like `https://my-computer.tailnet-name.ts.net`.
3. Start the editor allowing that name: `flosub serve --allow-host my-computer.tailnet-name.ts.net` (use the name without `https://`).
4. Open that `https` address on the phone and type the same password.

On Linux, if `tailscale serve` complains about permissions, run once: `sudo tailscale set --operator=$USER`.

Do **not** use `tailscale funnel`: it publishes the editor on the whole internet. `tailscale serve` stays inside your private network.

## Self-hosted: Headscale

[Headscale](https://headscale.net) is an open-source server that does the job of Tailscale's coordination service, on a machine you run yourself. Once your devices are connected to it, the steps are the same as for Tailscale: reach the computer by its name or its `100.x.y.z` address, start the editor with `--allow-host <that name>` when you use a name, and use the same password. Setting up a Headscale server is outside this guide: see its documentation.

## Settings you can edit

`flosub auth status` prints the path of `access.json`. Besides the hashed password it has switches you can change with a text editor (restart the editor afterwards):

| Switch | Default | Meaning |
|---|---|---|
| `lan` | `true` | With a password, listen on the local network. `false` keeps the editor on this computer only, whatever the password. |
| `require_password_here` | `false` | `true` asks for the password on this computer too (a shared computer). |
| `allow_public` | `false` | `true` accepts connections from public internet addresses. Not recommended. |

## Never open a port on your router

Do not forward a port from the internet to the editor. Use Tailscale or Headscale to go outside: they are made for it. If a port is open anyway, the editor refuses public addresses by default.

## Technical reference

The design and the threat model are in [ADR-026](dev-docs/decisions/ADR-026-network-access-password-and-launcher.md).
