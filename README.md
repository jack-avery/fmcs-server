# fmcs-server

Basic Ansible playbooks for Forge Minecraft servers

Found the playbooks useful? [Buy me a coffee ☕](https://ko-fi.com/raspy)!

## Usage

Ansible requires Linux. If you're running Windows, consider setting up WSL.

1. Run `pip install -r requirements.txt` to install Python requirements.
2. Ensure you have Ansible and Docker installed on your machine.
3. Ensure your Ansible Hosts have Docker installed, and a user named `mc` with the `docker` role.

### Creating servers
1. Build your Ansible inventory and global/host variables using the samples:
> todo
2. Trigger `make fmcs` to build images and run servers.

### Updating ops/whitelist
1. Trigger `make perms`.<br/>
-- Define ops in `mc.secret.yml`<br/>
-- Define whitelists in `{host}.secret.yml`

## Pre-commit

There is a pre-commit hook that you should enable to ensure you don't commit any unencrypted secret:<br/>
`ln .hooks/pre-commit .git/hooks/pre-commit`
