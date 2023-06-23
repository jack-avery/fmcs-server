.PHONY: all fmcs

all: fmcs

fmcs:
	@ansible-playbook playbooks/fmcs.yml

perms:
	@ansible-playbook playbooks/perms.yml

atl:
	@python atl_manis.py
