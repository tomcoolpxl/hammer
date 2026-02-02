#!/bin/bash

echo "🔥 Vagrant + VirtualBox Nuke Script"

# Kill any VirtualBox processes that may lock VMs
echo "🧨 Killing VirtualBox processes..."
pkill -f VirtualBox
pkill -f VBoxHeadless
pkill -f vboxmanage

# Step 1: Try to destroy all Vagrant VMs nicely
echo "🧹 Cleaning up Vagrant-managed VMs..."
vagrant global-status --prune | awk '/virtualbox/ {print $1, $5}' | while read -r id dir; do
    if [ -d "$dir" ]; then
        echo "➡️ Destroying $id in $dir"
        (cd "$dir" && vagrant destroy -f "$id")
    else
        echo "⚠️  Directory missing for $id — skipping Vagrant destroy"
    fi
done

# Step 2: Force remove any leftover VMs from VirtualBox
echo "💣 Unregistering all VirtualBox VMs..."
VBoxManage list vms | awk -F\" '{print $2}' | while read -r vm; do
    echo "➡️ Trying to unregister and delete $vm"
    VBoxManage unregistervm "$vm" --delete 2>&1 | tee /tmp/vbox_cleanup.log
done

# Step 3: Handle locked VMs from failed unregisters
echo "🔍 Scanning for locked VMs..."
grep "locked" /tmp/vbox_cleanup.log | awk -F"'" '{print $2}' | while read -r locked_vm; do
    echo "🚨 Found locked VM: $locked_vm"
    echo "➡️ Forcing removal of $locked_vm"

    # Find the UUID
    vm_uuid=$(VBoxManage showvminfo "$locked_vm" | grep "UUID:" | awk '{print $2}')

    # Try forced close and removal
    VBoxManage controlvm "$locked_vm" poweroff
    sleep 1
    VBoxManage unregistervm "$locked_vm" --delete
done

echo "🧼 Final vagrant prune..."
vagrant global-status --prune

echo "✅ All Vagrant + VirtualBox VMs cleaned."
