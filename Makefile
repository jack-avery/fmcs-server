.PHONY: all fmcs

all: fmcs relay cron

fmcs:
	@ansible-playbook playbooks/fmcs.yml

perms:
	@ansible-playbook playbooks/perms.yml

backup:
	@ansible-playbook playbooks/backup.yml

relay:
	@ansible-playbook playbooks/relay.yml

cron:
	@ansible-playbook playbooks/cron.yml

atl:
	@python atl_manis.py
