# fmcs-server

Automatic set-up [Fabric](https://fabricmc.net/) modded Minecraft dedicated servers, supporting identical exports for use with [ATLauncher](https://atlauncher.com/)

Found the playbooks useful? [Buy me a coffee ☕](https://ko-fi.com/raspy)!

## Usage

Ansible requires Linux. If you're running Windows, consider setting up WSL.

1. Run `pip install -r requirements.txt` to install Python requirements.
2. Ensure you have Ansible and Docker installed on your machine.
3. Ensure your Ansible Hosts have Docker installed, and a user named `mc` with the `docker` role.

### Creating servers
1. Build your Ansible inventory and global/host variables using the samples:
> * host_vars/host.secret.yml.sample
> * host_vars/host.yml.sample
2. Trigger `make fmcs` to build images and run servers.

### Updating ops/whitelist
1. Trigger `make perms`.<br/>
-- Define ops/whitelist in `{host}.secret.yml`

### Creating ATLauncher instance .zip
1. Trigger `make atl`.<br/>
-- The manifests are put into the `out` folder

## TODO
* define users for whitelist/op as only UUID/username
* define mods as only mod page
* improve and simplify customization of server.properties

## Pre-commit
There is a pre-commit hook that you should enable to ensure you don't commit any unencrypted secret:<br/>
`ln .hooks/pre-commit .git/hooks/pre-commit`
