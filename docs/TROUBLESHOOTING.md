# HAMMER Troubleshooting

## Common Issues

### Vagrant / libvirt

**"vagrant not found"**
```bash
# Install Vagrant
# Fedora/RHEL: sudo dnf install vagrant
# Ubuntu: sudo apt install vagrant
# macOS: brew install vagrant
```

**"vagrant-libvirt plugin not installed"**
```bash
vagrant plugin install vagrant-libvirt
```

**"Error while connecting to libvirt"**
```bash
# Ensure libvirt is running
sudo systemctl start libvirtd
sudo systemctl enable libvirtd

# Add user to libvirt group
sudo usermod -aG libvirt $USER
# Then log out and back in
```

**VMs stuck or unresponsive**
```bash
# From the grading bundle directory:
vagrant destroy -f
vagrant up
```

### Ansible

**"ansible-playbook not found"**
```bash
pip install ansible
# Or check it's in your PATH:
which ansible-playbook
```

**SSH connection failures**
```bash
# Check VM status
vagrant status

# Test connectivity
ansible all -i inventory/hosts.yml -m ping

# If using a custom key:
ansible all -i inventory/hosts.yml -m ping --private-key=.vagrant/machines/*/libvirt/private_key
```

**Playbook timeout**
```bash
# Increase timeout via environment variable
export HAMMER_PLAYBOOK_TIMEOUT=1200  # 20 minutes
hammer grade --spec spec.yaml --student-repo . --out results/
```

### Build Issues

**"Path traversal detected"**
Your spec contains a path with `..` components or shell metacharacters. Fix the path in your spec YAML.

**"Too many nodes"**
HAMMER supports a maximum of 245 nodes per assignment (limited by /24 subnet).

### Grading Issues

**"Grading bundle not found"**
When using `--skip-build`, ensure the grading bundle exists at the expected path. Run without `--skip-build` first.

**Low scores / unexpected failures**
1. Check `results/baseline/converge.log` for Ansible errors
2. Check `results/baseline/test.log` for test failures
3. Run with `--verbose` for detailed output
4. Check `results/report.json` for the full report

### Disk Space

Each VM uses ~1-2 GB. Clean up after grading:
```bash
# From grading bundle directory
vagrant destroy -f

# Remove all HAMMER vagrant boxes
vagrant box list | grep alma | awk '{print $1}' | xargs -I{} vagrant box remove {}
```
