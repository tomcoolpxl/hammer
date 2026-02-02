# PXL Ansible Examen

## Shellscripts

* `deploy.sh`: Bereidt de examenomgeving voor door VMs te stoppen, de omgeving op te kuisen en het Ansible-playbook uit te voeren.

* `run_ansible.sh`: Voert het Ansible-playbook uit.

* `check_config.sh`: ONVOLLEDIG script dat bepaalde files en configuraties checkt op de target vm.


* `package_exam.sh`: Bereidt de examenoplossing voor om in te dienen en berekent de SHA-256-hash.


### Hulpscripts

* `nuke_all_vms.sh`: Verwijdert alle VirtualBox-VMs geforceerd om een propere startomgeving te garanderen.
* `clean_known_hosts.sh`: Verwijdert SSH host keys voor lokale VM-verbindingen om SSH-problemen te vermijden.
