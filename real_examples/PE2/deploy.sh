#!/bin/bash

# Remove old SSH known hosts entries to avoid conflicts
ssh-keygen -R [127.0.0.1]:2222
ssh-keygen -R [127.0.0.1]:2200

# Destroy and recreate VMs
vagrant destroy -f
vagrant up
