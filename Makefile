.PHONY: all servers test

all: servers relay cron

servers:
	@ansible-playbook playbooks/servers.yml

perms:
	@ansible-playbook playbooks/perms.yml

backup:
	@ansible-playbook playbooks/backup.yml

relay: mrpack
	@ansible-playbook playbooks/relay.yml

cron:
	@ansible-playbook playbooks/cron.yml

test: mrpack
	@ansible-playbook playbooks/test.yml

mrpack:
	@python3 mrpack.py
