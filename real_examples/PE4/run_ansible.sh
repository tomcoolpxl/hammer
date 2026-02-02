#!/bin/bash

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}${MAGENTA}=== RUNNING ANSIBLE PLAYBOOK ===${RESET}"
echo -e "${YELLOW}Starting playbook execution...${RESET}\n"

# Run Ansible with colored output
ANSIBLE_FORCE_COLOR=true ansible-playbook playbook.yml -v

# Check exit status
if [ $? -eq 0 ]; then
    echo -e "\n${BOLD}${GREEN}✓ Playbook execution completed successfully!${RESET}"
else
    echo -e "\n${BOLD}${RED}✗ Playbook execution failed!${RESET}"
fi

echo -e "${BOLD}${MAGENTA}=== ANSIBLE PLAYBOOK EXECUTION COMPLETE ===${RESET}"