#!/bin/bash

# Run all Ansible playbooks
echo "Running main playbook..."
ansible-playbook -i inventory.ini playbook.yml

echo "Running extras playbooks..."
ansible-playbook -i inventory.ini playbook_loops.yml
ansible-playbook -i inventory.ini playbook_conditionals.yml
ansible-playbook -i inventory.ini playbook_retries.yml
ansible-playbook -i inventory.ini playbook_common.yml
ansible-playbook -i inventory.ini playbook_vault.yml --vault-password-file=.vault_pass

echo "All playbooks executed."