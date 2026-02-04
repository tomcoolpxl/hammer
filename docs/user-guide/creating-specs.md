# Creating HAMMER Specifications

The HAMMER specification is a YAML file that defines everything about an assignment.

## Top-level Fields

- `assignment_id`: Unique identifier for the assignment (e.g., `pe1-pyramid-app`).
- `assignment_version`: Version of the assignment (e.g., `1.0`).
- `seed`: Integer used for deterministic network and variable generation.
- `provider`: Virtualization provider (currently only `libvirt`).
- `os`: Operating system (currently only `almalinux9`).

## Topology

Define the nodes in your lab:

```yaml
topology:
  domain: "example.local"
  nodes:
    - name: "server0"
      groups: ["webservers", "database"]
      resources:
        cpu: 1
        ram_mb: 1024
      forwarded_ports:
        - host_port: 8080
          guest_port: 80
          protocol: tcp
```

## Variable Contracts

Test student variable usage and precedence:

```yaml
variable_contracts:
  - name: "http_port"
    description: "The port the web server listens on"
    defaults:
      student: 80
      baseline: 80
      mutation: 8080
    weight: 10.0
```

## Behavioral Contracts

Verify system state after Ansible execution:

```yaml
behavioral_contracts:
  packages:
    - name: "httpd"
      state: present
      node_selector: { group: "webservers" }

  services:
    - name: "httpd"
      enabled: true
      running: true
      node_selector: { group: "webservers" }

  files:
    - items:
        - path: "/var/www/html/index.html"
          content_contains: ["Welcome"]
      node_selector: { host: "server0" }
```

### Phase-Specific Contracts

You can restrict a contract to specific phases:

```yaml
  services:
    - name: "iptables"
      enabled: true
      phases: [mutation, idempotence] # Only check after mutation phase
```
