<div align="center">

# fmcs-server

</div>

Automatic set-up [Fabric](https://fabricmc.net/) or [Forge](https://forums.minecraftforge.net/) modded Minecraft dedicated servers, supporting `.mrpack` exports for import with [ATLauncher](https://atlauncher.com/) and a Server <-> Discord relay bot.

Found the playbooks useful? [Buy me a coffee ☕](https://ko-fi.com/raspy)!

## How to Use ✍️

Ansible requires **Linux**. If you're running Windows, consider setting up [**WSL**](https://learn.microsoft.com/en-us/windows/wsl/install).

In this folder in Linux or WSL (instructions are for Ubuntu):

1. Run `sudo apt-get update && sudo apt-get upgrade`
2. Install Python and Pip: `sudo apt-get install python3 python3-pip`
3. Install Python requirements: `pip install -r requirements.txt`
4. Ensure your servers have Python and Docker installed, and a user named `fmcs` with the `docker` role.
> If you are hosting on your own machine, you must have Python, Ansible and Docker installed on your machine<br/>
> [Here is the docs for installing Docker in WSL](https://docs.docker.com/desktop/install/ubuntu/)
5. Build your Ansible inventory and global/host variables using the samples:
> * host_vars/mc.myhost.com.secret.yml.sample
> * host_vars/mc.myhost.com.yml.sample
> * inventory.yml.sample
6. Ansible supports encrypted data vaults. Rename `.vault_pass.sh.sample` to `.vault_pass.sh` and put your vault key in. Even if you're not using vaults, the file **must still exist**!

### Creating servers
2. Trigger `make servers` to build images and run servers.<br/>
-- Save the server icon(s) you want as `roles/servers/files/{host}/{instance}.png`

### Updating ops/whitelist
1. Trigger `make perms`.<br/>
-- Define ops/whitelist in `{host}.yml`

### Creating ATLauncher .mrpacks
1. Trigger `make mrpack`.<br/>
-- The files are put into the `mrpacks` folder

### Running relay bots
1. Ensure you have the required setup:
* Discord bot token
* Guild (Server) and Channel ID
2. Trigger `make relay`.<br/>

### Backing up worlds
1. Trigger `make backup`.<br/>
-- Backups will appear in `roles/backup/files/{host}`

## 🔌 Ports
`fmcs-server` bases all used ports off of `mcs_base_port`; default `25565`.<br/>
Every server reserves `mcs_reserve_ports` ports for itself; default `10`.
> e.g. if you have multiple servers on one machine, they would be: `25565`, `25575`, etc...

A list of ports, relative to `mcs_base_port`:
- `+0 (UDP/TCP)`: Main server
- `+1     (TCP)`: Rcon *(the relay bot does **not** need this to port to be open on the host machine to work!)*
- `+2     (UDP)`: Port opened for voice chat mods such as [Simple Voice Chat](https://modrinth.com/plugin/simple-voice-chat)
- `+3     (TCP)`: Autoconfigured for [Dynmap](https://github.com/webbukkit/dynmap/)

## Pre-commit 🛡️
There is a pre-commit hook that you should enable to ensure you don't commit any unencrypted secret:<br/>
`ln .hooks/pre-commit .git/hooks/pre-commit`

## Bug reports & feature suggestions 🐛
Has something gone **horribly** wrong? *Or do you just think something's missing?*

Feel free to [create a new issue](https://github.com/jack-avery/fmcs-server/issues), join the [Discord](https://discord.gg/qpyT4zx), or message me directly on Discord about it: `raspy#0292`.

> If you're reporting a bug, it's most useful to me if you can find a way to consistently replicate the issue.<br/>
