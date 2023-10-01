.PHONY: all servers test

all: servers relay cron

servers:
	@ansible-playbook playbooks/servers.yml

perms:
	@ansible-playbook playbooks/perms.yml

backup:
	@ansible-playbook playbooks/backup.yml

relay:
	@python3 atl_manis.py
	@ansible-playbook playbooks/relay.yml

cron:
	@ansible-playbook playbooks/cron.yml

test:
	@ansible-playbook playbooks/test.yml

atl:
	@python3 atl_manis.py
