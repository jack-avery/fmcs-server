<div align="center">

# fmcs-server

</div>

Automatic set-up [Fabric](https://fabricmc.net/) or [Forge](https://forums.minecraftforge.net/) modded Minecraft dedicated servers, supporting manifest exports for installation with [ATLauncher](https://atlauncher.com/) and a Server <-> Discord relay bot.

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
> * host_vars/my_host.secret.yml.sample
> * host_vars/my_host.yml.sample
> * inventory.yml.sample
6. Ansible supports encrypted data vaults. Echo the Ansible vault key you're using in `.vault_pass.sh`. Even if you're not using vaults, the file **must still exist**!
> Setting up the daily restart "cronjob" automatically requires that you echo the password for the `root` user in a script named `.become_pass.sh` in this folder.

```sh
#!/bin/bash
# Sample .become_pass.sh or .vault_pass.sh
echo vault_or_root_pass
```

### Creating servers
2. Trigger `make servers` to build images and run servers.<br/>
-- Save the server icon(s) you want as `roles/servers/files/{host}/{instance}.png`

### Updating ops/whitelist
1. Trigger `make perms`.<br/>
-- Define ops/whitelist in `{host}.yml`

### Running relay bots
1. Ensure you have the required setup:
* Discord bot token
* Guild (Server) and Channel ID
2. Trigger `make relay`.<br/>

### Backing up worlds
1. Trigger `make backup`.<br/>
-- Backups will appear in `roles/backup/files/{host}`

### Creating ATLauncher instance .zip
1. Trigger `make atl`.<br/>
-- The manifests are put into the `out` folder

## 🔌 Ports
`fmcs-server` bases all used ports off of `mcs_base_port` in `group_vars/all.yml`.<br/>
By default, this is set to `25565`, which is standard for Minecraft servers.<br/>
A list of ports, relative to `mcs_base_port`:
- `+0 (UDP/TCP)`: Main server
- `+1     (TCP)`: Rcon *(the relay bot does **not** need this to port to be open on the host machine to work!)*
- `+2     (UDP)`: Port opened for voice chat mods

Every server adds **10** to port number, so if you had two servers on one machine, the second can be connected to using `:25575`.<br/>

## Pre-commit 🛡️
There is a pre-commit hook that you should enable to ensure you don't commit any unencrypted secret:<br/>
`ln .hooks/pre-commit .git/hooks/pre-commit`

## Bug reports & feature suggestions 🐛
Has something gone **horribly** wrong? *Or do you just think something's missing?*

Feel free to [create a new issue](https://github.com/jack-avery/fmcs-server/issues), join the [Discord](https://discord.gg/qpyT4zx), or message me directly on Discord about it: `raspy#0292`.

> If you're reporting a bug, it's most useful to me if you can find a way to consistently replicate the issue.<br/>
