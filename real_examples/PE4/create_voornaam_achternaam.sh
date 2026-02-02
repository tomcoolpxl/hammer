#!/bin/bash

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}${CYAN}=== CREATING EXAM SUBMISSION PACKAGE ===${RESET}"

# Get current directory name (project root)
CURRENT_DIR=$(basename "$PWD")

# Replace this with your actual name
NAME="voornaam_achternaam"

# Create the tar file in the current directory
echo -e "${YELLOW}Creating tarball...${RESET}"
tar -czf "$NAME.tgz" \
    --exclude='./.vagrant' \
    --exclude='./create_voornaam_achternaam.sh' \
    --transform="s/$CURRENT_DIR/$NAME/" \
    .

echo -e "\n${GREEN}Package created: ${BOLD}$NAME.tgz${RESET}"
