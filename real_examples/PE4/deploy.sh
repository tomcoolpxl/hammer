#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Print header
echo -e "${BOLD}${BLUE}=== PXL EXAM ENVIRONMENT SETUP ===${RESET}"
echo -e "${YELLOW}Starting environment setup process...${RESET}\n"

# Stop running VMs first
echo -e "${BOLD}${CYAN}[STEP 1]${RESET} ${GREEN}Stopping any running Vagrant VMs...${RESET}"
vagrant destroy -f 
echo -e "\n"

# Run nuke script
echo -e "${BOLD}${CYAN}[STEP 2]${RESET} ${GREEN}Running nuke_all_vms.sh to ensure clean environment...${RESET}"
chmod +x ./nuke_all_vms.sh
./nuke_all_vms.sh
echo -e "\n"

# Clean known hosts
echo -e "${BOLD}${CYAN}[STEP 3]${RESET} ${GREEN}Cleaning known hosts to prevent SSH issues...${RESET}"
chmod +x ./clean_known_hosts.sh
./clean_known_hosts.sh
echo -e "\n"

# Create VMs
echo -e "${BOLD}${CYAN}[STEP 4]${RESET} ${GREEN}Creating new VMs from Vagrantfile...${RESET}"
vagrant up
echo -e "\n"

# Run Ansible
echo -e "${BOLD}${CYAN}[STEP 5]${RESET} ${GREEN}Running Ansible playbook...${RESET}"
chmod +x ./run_ansible.sh
./run_ansible.sh
echo -e "\n"

echo -e "${BOLD}${BLUE}=== ENVIRONMENT SETUP COMPLETE ===${RESET}"