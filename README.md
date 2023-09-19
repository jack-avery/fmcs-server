<div align="center">

# fmcs-server

</div>

Automatic set-up [Fabric](https://fabricmc.net/) modded Minecraft dedicated servers, supporting identical exports for use with [ATLauncher](https://atlauncher.com/) and a Server <-> Discord relay bot.

Found the playbooks useful? [Buy me a coffee ☕](https://ko-fi.com/raspy)!

## How to Use ✍️

Ansible requires **Linux**. If you're running Windows, consider setting up [**WSL**](https://learn.microsoft.com/en-us/windows/wsl/install).

1. Run `pip install -r requirements.txt` to install Python requirements.
2. Ensure you have Ansible installed on your machine.
3. Ensure your Ansible Hosts have Docker installed, and a user named `fmcs` with the `docker` role.
> If you are hosting on your own machine, you must have Ansible and Docker installed on your machine<br/>
> [Here is the docs for installing Docker in WSL](https://docs.docker.com/desktop/install/ubuntu/)
4. Build your Ansible inventory and global/host variables using the samples:
> * host_vars/my_host.secret.yml.sample
> * host_vars/my_host.yml.sample
> * inventory.yml.sample
5. If you plan on using Ansible vaults, echo the key in `.vault_pass.sh`.
> If you're not using vaults, the file must still exist so that Ansible doesn't panic, even if it's empty
6. Setting up the daily restart automatically requires that you echo the password for the `root` user in a script named `.become_pass.sh` in this folder:
```sh
#!/bin/bash
# .become_pass.sh
echo my_root_password
```

### Creating servers
2. Trigger `make fmcs` to build images and run servers.

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

## Pre-commit 🛡️
There is a pre-commit hook that you should enable to ensure you don't commit any unencrypted secret:<br/>
`ln .hooks/pre-commit .git/hooks/pre-commit`

## Bug reports & feature suggestions 🐛
Has something gone **horribly** wrong? *Or do you just think something's missing?*

Feel free to [create a new issue](https://github.com/jack-avery/fmcs-server/issues), join the [Discord](https://discord.gg/qpyT4zx), or message me directly on Discord about it: `raspy#0292`.

> If you're reporting a bug, it's most useful to me if you can find a way to consistently replicate the issue.<br/>
