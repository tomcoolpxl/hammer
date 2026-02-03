# Hammer Gap Analysis for PE3 Assignment

## Executive Summary

PE3 is a single-VM nginx webserver configuration assignment. Comparing PE3 requirements
against Hammer's current capabilities reveals that **most features are already supported**.
The main gap is **handler test generation**.

**Status Summary:**

| Feature | Status | Priority | Effort |
|---------|--------|----------|--------|
| Single VM with domain/FQDN | SUPPORTED | - | - |
| Package contracts (nginx, firewalld) | SUPPORTED | - | - |
| Service contracts | SUPPORTED | - | - |
| File contracts (directories, files, content) | SUPPORTED | - | - |
| Firewall contracts | SUPPORTED | - | - |
| HTTP endpoint testing | SUPPORTED | - | - |
| Variable contracts with bindings | SUPPORTED | - | - |
| **Handler test generation** | **MISSING** | HIGH | 3h |

---

## PE3 Requirements Analysis

### Infrastructure (All Supported)

| Requirement | Hammer Feature | Status |
|-------------|---------------|--------|
| Single VM (server0) | topology.nodes | SUPPORTED |
| FQDN (server0.pxldemo.local) | topology.domain | SUPPORTED |
| Port forwarding (80 -> 8888) | node.forwarded_ports | SUPPORTED |
| /etc/hosts provisioning | Vagrantfile.j2 shell provisioner | SUPPORTED |

### Minimum Requirements (10/20) - All Supported

| Requirement | Hammer Feature | Status |
|-------------|---------------|--------|
| Install nginx package | packages contract | SUPPORTED |
| Install firewalld package | packages contract | SUPPORTED |
| nginx service enabled/running | services contract | SUPPORTED |
| firewalld service enabled/running | services contract | SUPPORTED |
| Create `/var/www/mypage/` directory | files contract (is_directory) | SUPPORTED |
| Create `/var/www/mypage/index.html` | files contract | SUPPORTED |
| Create `/etc/nginx/conf.d/mypage.conf` | files contract | SUPPORTED |
| Open port 8080 in firewall | firewall contract | SUPPORTED |
| Variable `doc_root` = `/var/www/mypage` | variable_contracts | SUPPORTED |
| Variable `web_port` = 8080 | variable_contracts | SUPPORTED |
| nginx listens on port 8080 | service_listen_port binding | SUPPORTED |
| HTTP response test | http_endpoints contract | SUPPORTED |

### Extra 1 (2 pts) - Variables - Supported

External `vars.yml` file with all variables. This is tested implicitly through
variable bindings - if variables work, they must be defined somewhere.

### Extra 2 (4 pts) - Conditionals - Supported

Conditional index.html creation (skip if exists). This is tested implicitly through
idempotence - running the playbook twice should produce no changes.

### Extra 3 (4 pts) - Handlers - **PARTIALLY SUPPORTED**

| Requirement | Status |
|-------------|--------|
| nginx restart on config change | Handler contracts DEFINED but **no test generation** |
| firewalld restart on rule change | Handler contracts DEFINED but **no test generation** |

**Gap:** Handler contracts exist in `spec.py` and `plan.py`, but there's no:
- `test_handlers.py.j2` template
- `generate_handler_tests()` function in `behavioral.py`
- Wiring in `testgen/__init__.py`

---

## Gap: Handler Test Generation

### Current State

Handler contracts are fully defined in the spec schema:

```python
class HandlerContract(BaseModel):
    handler_name: NonEmptyStr
    node_selector: NodeSelector
    handler_target: HandlerTarget  # service + action (restart/reload)
    trigger_conditions: List[Trigger]  # file_changed, template_changed, variable_changed
    non_trigger_conditions: List[NonTrigger]  # noop_rerun, unrelated_file_changed
    expected_runs: ExpectedRunsSet  # baseline, mutation, idempotence expectations
    weight: float = Field(default=2.0, ge=0.0)
```

Handler plans are built in `plan.py`:

```python
class HandlerPlan(BaseModel):
    handler_name: str
    host_targets: List[str]
    service: str
    action: str
    expectations: Dict[ExecutionPhaseName, HandlerPhaseExpectation]
    weight: float
```

**But no tests are generated!**

### What's Needed

1. **Create `test_handlers.py.j2` template**
   - Test that handler runs when trigger condition is met
   - Test that handler doesn't run when non-trigger condition is met
   - Use Ansible callback plugins or log parsing to detect handler execution

2. **Add `generate_handler_tests()` to `behavioral.py`**

3. **Wire up in `testgen/__init__.py`**

### Handler Testing Strategy

Testing handlers is tricky because you need to:
1. Run the playbook
2. Parse the output to see if handlers were notified/executed
3. Verify against expectations

This may require changes to the runner, not just test generation.

**Alternative approach:** Instead of testing handler execution directly, test the
*effect* of handlers:
- After changing nginx config, verify nginx has reloaded (check process start time or config hash)
- After changing firewall rules, verify firewalld has restarted

---

## PE3 Spec Draft (Without Handler Tests)

Even without handler test generation, we can create a functional PE3 spec that tests
all the behavioral contracts:

```yaml
assignment_id: "pe3-nginx-webserver"
assignment_version: "2026.02"
spec_version: "1.0"
seed: 42
provider: "libvirt"
os: "almalinux9"

features:
  vault: false
  selinux: false
  handlers: true  # Enable handler contracts (even if not fully tested)
  reachability: false

topology:
  domain: "pxldemo.local"
  nodes:
    - name: "server0"
      groups: ["all", "webservers"]
      resources:
        cpu: 1
        ram_mb: 1024
      forwarded_ports:
        - host_port: 8888
          guest_port: 8080
          protocol: tcp

entrypoints:
  playbook_path: "playbook.yml"
  required_files:
    - "playbook.yml"
  provided_files:
    - source: "landing-page.html.j2"
      destination: "templates/landing-page.html.j2"
    - source: "nginx.conf"
      destination: "nginx.conf.example"

variable_contracts:
  - name: "web_port"
    type: "int"
    defaults:
      student: 8080
    allowed_values: [8080, 9090]
    grading_overlay_targets:
      - overlay_kind: "group_vars"
        target_name: "webservers"
    binding_targets:
      - type: "service_listen_port"
        weight: 2.0
        target:
          service: "nginx"
          protocol: "tcp"
          address: "0.0.0.0"
      - type: "firewall_port_open"
        weight: 2.0
        target:
          zone: "public"
          protocol: "tcp"

behavioral_contracts:
  packages:
    - name: "nginx"
      state: "present"
      node_selector: { group: "webservers" }
      weight: 3.0
    - name: "firewalld"
      state: "present"
      node_selector: { group: "webservers" }
      weight: 2.0

  services:
    - name: "nginx"
      enabled: true
      running: true
      node_selector: { group: "webservers" }
      weight: 3.0
    - name: "firewalld"
      enabled: true
      running: true
      node_selector: { group: "webservers" }
      weight: 2.0

  files:
    # Document root directory
    - items:
        - path: "/var/www/mypage"
          present: true
          is_directory: true
      node_selector: { group: "webservers" }
      weight: 2.0
    # Index.html from template
    - items:
        - path: "/var/www/mypage/index.html"
          present: true
          content_regex: "page_title|page_description"
      node_selector: { group: "webservers" }
      weight: 2.0
    # nginx config file
    - items:
        - path: "/etc/nginx/conf.d/mypage.conf"
          present: true
          content_regex: "listen.*8080|/var/www/mypage"
      node_selector: { group: "webservers" }
      weight: 3.0

  firewall:
    - open_ports:
        - port: { var: "web_port" }
          protocol: "tcp"
          zone: "public"
      firewall_type: "firewalld"
      node_selector: { group: "webservers" }
      weight: 3.0

  http_endpoints:
    - url: "http://localhost:8080/"
      method: "GET"
      expected_status: 200
      response_contains: "page_title"
      timeout_seconds: 10
      node_selector: { host: "server0" }
      weight: 5.0

# Handler contracts defined but not tested yet
handler_contracts:
  - handler_name: "restart nginx"
    node_selector: { group: "webservers" }
    handler_target:
      service: "nginx"
      action: "restart"
    trigger_conditions:
      - template_changed: "/etc/nginx/conf.d/mypage.conf"
    non_trigger_conditions:
      - noop_rerun: true
    expected_runs:
      baseline: "at_least_once"
      mutation: "at_least_once"
      idempotence: "zero"
    weight: 2.0
  - handler_name: "restart firewalld"
    node_selector: { group: "webservers" }
    handler_target:
      service: "firewalld"
      action: "restart"
    trigger_conditions:
      - variable_changed: "web_port"
    non_trigger_conditions:
      - noop_rerun: true
    expected_runs:
      baseline: "at_least_once"
      mutation: "at_least_once"
      idempotence: "zero"
    weight: 2.0

idempotence:
  required: true
  enforcement:
    require_changed_zero: true
    require_no_handlers: true

phase_overlays:
  baseline:
    group_vars:
      webservers:
        web_port: 8080
        doc_root: "/var/www/mypage"
        page_title: "My Page"
        page_description: "Created with Ansible"
  mutation:
    group_vars:
      webservers:
        web_port: 9090
        doc_root: "/var/www/mypage"
        page_title: "My Page"
        page_description: "Created with Ansible"
```

---

## Implementation Plan

### Phase 1: Create Working PE3 Spec (No Handler Tests)

1. Create `spec.yaml` based on draft above
2. Create solution playbook that passes all contracts
3. Test locally: `vagrant up`, run playbook, verify
4. Verify all behavioral tests pass

**Estimated effort:** 2 hours

### Phase 2: Add Handler Test Generation (Optional)

1. Create `test_handlers.py.j2` template
2. Add `generate_handler_tests()` to `behavioral.py`
3. Wire up in `testgen/__init__.py`
4. Update runner to capture handler execution from Ansible output
5. Add unit tests

**Estimated effort:** 3-4 hours

---

## Verification Strategy

1. **Unit tests**: Existing tests should still pass
2. **Build test**: `hammer build real_examples/PE3/spec.yaml`
3. **Local VM test**: `vagrant up`, run solution playbook
4. **Behavioral tests**: Run generated pytest tests against solution
5. **Mutation test**: Change `web_port` to 9090, verify playbook adapts
6. **Idempotence test**: Run playbook twice, verify no changes

---

## Summary

PE3 is **95% supported** by current Hammer. The only gap is handler test generation,
which is a "nice to have" for Extra 3 (4 points). All minimum requirements and most
extra requirements can be tested with existing features.

| Priority | Task | Effort |
|----------|------|--------|
| HIGH | Create PE3 spec and solution playbook | 2h |
| MEDIUM | Add handler test generation | 3-4h |
