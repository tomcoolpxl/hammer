#!/bin/bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Server connection settings
SERVER="server0.pxldemo.local"
SSH_CMD="ssh -i ~/.vagrant.d/insecure_private_key -p 2222 vagrant@127.0.0.1"

echo -e "${BOLD}${MAGENTA}=== PXL EXAM CONFIGURATION CHECK ===${RESET}"
echo -e "${YELLOW}Running checks on ${CYAN}$SERVER${RESET}...\n"

# Question 1 check - Users
echo -e "${BOLD}${BLUE}Question 1 - User Creation${RESET}"
echo -e "${CYAN}Checking if users exist and are in students group...${RESET}"

for user in carol dave edgar; do
    echo -ne "User ${BOLD}$user${RESET}: "
    if $SSH_CMD "id $user" > /dev/null 2>&1; then
        echo -ne "${GREEN}✓ exists${RESET}"
        
        if $SSH_CMD "groups $user | grep -q students"; then
            echo -ne " ${GREEN}✓ in students group${RESET}"
        else
            echo -ne " ${RED}✗ NOT in students group${RESET}"
        fi
        
        if $SSH_CMD "test -d /home/$user"; then
            echo -e " ${GREEN}✓ has home directory${RESET}"
        else
            echo -e " ${RED}✗ NO home directory${RESET}"
        fi
    else
        echo -e "${RED}✗ does NOT exist${RESET}"
    fi
done
echo ""

# Question 2 check - MOTD file
echo -e "${BOLD}${BLUE}Question 2 - MOTD File${RESET}"
echo -e "${CYAN}Checking if /etc/motd exists with correct content and permissions...${RESET}"

if $SSH_CMD "test -f /etc/motd"; then
    echo -e "MOTD file: ${GREEN}✓ exists${RESET}"
    
    echo -e "\n${CYAN}Content:${RESET}"
    $SSH_CMD "cat /etc/motd"
    echo ""
    
    OWNER=$($SSH_CMD "stat -c '%U' /etc/motd")
    GROUP=$($SSH_CMD "stat -c '%G' /etc/motd")
    PERMS=$($SSH_CMD "stat -c '%A' /etc/motd")
    
    echo -ne "Ownership: "
    if [ "$OWNER" == "edgar" ]; then
        echo -ne "${GREEN}✓ owner is edgar${RESET}"
    else
        echo -ne "${RED}✗ owner is $OWNER (should be edgar)${RESET}"
    fi
    
    if [ "$GROUP" == "students" ]; then
        echo -e " ${GREEN}✓ group is students${RESET}"
    else
        echo -e " ${RED}✗ group is $GROUP (should be students)${RESET}"
    fi
    
    echo -ne "Permissions: "
    if [ "$PERMS" == "-rw-rw-r--" ]; then
        echo -e "${GREEN}✓ correct permissions ($PERMS)${RESET}"
    else
        echo -e "${RED}✗ incorrect permissions: $PERMS (should be -rw-rw-r--)${RESET}"
    fi
else
    echo -e "MOTD file: ${RED}✗ does NOT exist${RESET}"
fi
echo ""

# Question 3 check - Systemd service
echo -e "${BOLD}${BLUE}Question 3 - Healthcheck Service${RESET}"
echo -e "${CYAN}Checking if healthcheck script and service exist...${RESET}"

if $SSH_CMD "test -f /opt/healthcheck.sh"; then
    PERMS=$($SSH_CMD "stat -c '%A' /opt/healthcheck.sh")
    echo -ne "Script /opt/healthcheck.sh: ${GREEN}✓ exists${RESET}"
    
    if [[ "$PERMS" == *"x"* ]]; then
        echo -e " ${GREEN}✓ is executable ($PERMS)${RESET}"
    else
        echo -e " ${RED}✗ NOT executable ($PERMS)${RESET}"
    fi
else
    echo -e "Script /opt/healthcheck.sh: ${RED}✗ does NOT exist${RESET}"
fi

if $SSH_CMD "test -f /etc/systemd/system/myhealthcheck.service"; then
    echo -e "Service file: ${GREEN}✓ exists${RESET}"
    
    echo -e "\n${CYAN}Service file content:${RESET}"
    $SSH_CMD "cat /etc/systemd/system/myhealthcheck.service"
    echo ""
    
    if $SSH_CMD "systemctl is-enabled myhealthcheck" > /dev/null 2>&1; then
        echo -e "Service enabled: ${GREEN}✓ yes${RESET}"
    else
        echo -e "Service enabled: ${RED}✗ no${RESET}"
    fi
    
    echo -e "\n${CYAN}Log file content:${RESET}"
    $SSH_CMD "test -f /var/log/healthcheck.log && cat /var/log/healthcheck.log || echo 'Log file does not exist'"
else
    echo -e "Service file: ${RED}✗ does NOT exist${RESET}"
fi
echo ""

# Question 4 check - Conditional files
echo -e "${BOLD}${BLUE}Question 4 - Conditional Files${RESET}"
echo -e "${CYAN}Checking if first_run.txt and second_run.txt exist...${RESET}"

if $SSH_CMD "test -f /opt/first_run.txt"; then
    echo -e "File /opt/first_run.txt: ${GREEN}✓ exists${RESET}"
    echo -e "\n${CYAN}Content:${RESET}"
    $SSH_CMD "cat /opt/first_run.txt"
    echo ""
else
    echo -e "File /opt/first_run.txt: ${RED}✗ does NOT exist${RESET}"
fi

if $SSH_CMD "test -f /opt/second_run.txt"; then
    echo -e "File /opt/second_run.txt: ${GREEN}✓ exists${RESET} (should only exist on second run)"
    echo -e "\n${CYAN}Content:${RESET}"
    $SSH_CMD "cat /opt/second_run.txt"
    echo ""
else
    echo -e "File /opt/second_run.txt: ${RED}✗ does NOT exist${RESET} (normal on first run)"
fi
echo ""

# Question 5 check - Failed creation
echo -e "${BOLD}${BLUE}Question 5 - Failure Test${RESET}"
echo -e "${CYAN}Checking if special file exists (should NOT exist)...${RESET}"

if $SSH_CMD "test -f /mnt/special/pxl/my_special_pxl_file"; then
    echo -e "File /mnt/special/pxl/my_special_pxl_file: ${RED}✗ EXISTS (should NOT exist)${RESET}"
else
    echo -e "File /mnt/special/pxl/my_special_pxl_file: ${GREEN}✓ does NOT exist (correct)${RESET}"
fi

echo -e "\n${BOLD}${MAGENTA}=== CONFIGURATION CHECK COMPLETE ===${RESET}"