.PHONY: all servers test

all: servers relay cron

servers:
	@ansible-playbook playbooks/servers.yml --extra-vars "only=$(ONLY)"

perms:
	@ansible-playbook playbooks/perms.yml --extra-vars "only=$(ONLY)"

backup:
	@ansible-playbook playbooks/backup.yml --extra-vars "only=$(ONLY)"

relay: mrpack
	@ansible-playbook playbooks/relay.yml --extra-vars "only=$(ONLY)"

cron:
	@ansible-playbook playbooks/cron.yml --extra-vars "only=$(ONLY)"

test:
	@ansible-playbook playbooks/test.yml --extra-vars "only=$(ONLY)"

mrpack:
	@python3 mrpack.py
