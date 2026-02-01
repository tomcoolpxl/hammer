## Spec schema v1.0

Below is a strict JSON Schema (Draft 2020-12) expressed in YAML. It is intentionally strict (additionalProperties: false almost everywhere) so mistakes fail fast.

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
$title: "HAMMER assignment spec v1.0"
$type: object
$defs:
  nonEmptyString:
    type: string
    minLength: 1

  featureFlags:
    type: object
    additionalProperties: false
    properties:
      vault: { type: boolean, default: false }
      selinux: { type: boolean, default: false }
      handlers: { type: boolean, default: true }
      reachability: { type: boolean, default: false }

  nodeResources:
    type: object
    additionalProperties: false
    required: [cpu, ram_mb]
    properties:
      cpu: { type: integer, minimum: 1, maximum: 64 }
      ram_mb: { type: integer, minimum: 256, maximum: 262144 }

  node:
    type: object
    additionalProperties: false
    required: [name, groups, resources]
    properties:
      name: { $ref: "#/$defs/nonEmptyString" }
      groups:
        type: array
        minItems: 0
        items: { $ref: "#/$defs/nonEmptyString" }
      resources: { $ref: "#/$defs/nodeResources" }

  forwardedPort:
    type: object
    additionalProperties: false
    required: [host_port, guest_port, protocol]
    properties:
      host_port: { type: integer, minimum: 1, maximum: 65535 }
      guest_port: { type: integer, minimum: 1, maximum: 65535 }
      protocol: { type: string, enum: [tcp, udp] }

  dependency:
    type: object
    additionalProperties: false
    required: [from_host, to_host, kind]
    properties:
      from_host: { $ref: "#/$defs/nonEmptyString" }
      to_host: { $ref: "#/$defs/nonEmptyString" }
      kind: { type: string, enum: [reachability, ordering] }

  topology:
    type: object
    additionalProperties: false
    required: [nodes]
    properties:
      nodes:
        type: array
        minItems: 1
        items: { $ref: "#/$defs/node" }
      forwarded_ports:
        type: array
        items: { $ref: "#/$defs/forwardedPort" }
      dependencies:
        type: array
        items: { $ref: "#/$defs/dependency" }

  entrypoints:
    type: object
    additionalProperties: false
    required: [playbook_path]
    properties:
      playbook_path: { $ref: "#/$defs/nonEmptyString" }
      required_roles:
        type: array
        items: { $ref: "#/$defs/nonEmptyString" }
      required_files:
        type: array
        items: { $ref: "#/$defs/nonEmptyString" }

  varType:
    type: string
    enum: [int, string, bool, list, dict]

  overlayKind:
    type: string
    enum: [group_vars, host_vars, inventory_vars]

  overlayTarget:
    type: object
    additionalProperties: false
    required: [overlay_kind, target_name]
    properties:
      overlay_kind: { $ref: "#/$defs/overlayKind" }
      target_name: { $ref: "#/$defs/nonEmptyString" }

  bindingMode:
    type: string
    enum: [all, any]

  bindingType:
    type: string
    enum:
      - service_listen_port
      - firewall_port_open
      - template_contains
      - file_contains
      - file_exists
      - file_mode
      - file_owner

  binding:
    type: object
    additionalProperties: false
    required: [type, target]
    properties:
      type: { $ref: "#/$defs/bindingType" }
      weight: { type: number, minimum: 0.0, default: 1.0 }
      target:
        oneOf:
          - type: object
            additionalProperties: false
            required: [service, protocol, address]
            properties:
              service: { $ref: "#/$defs/nonEmptyString" }
              protocol: { type: string, enum: [tcp, udp] }
              address: { $ref: "#/$defs/nonEmptyString" }
          - type: object
            additionalProperties: false
            required: [zone, protocol]
            properties:
              zone: { $ref: "#/$defs/nonEmptyString" }
              protocol: { type: string, enum: [tcp, udp] }
          - type: object
            additionalProperties: false
            required: [path, pattern]
            properties:
              path: { $ref: "#/$defs/nonEmptyString" }
              pattern: { $ref: "#/$defs/nonEmptyString" }
          - type: object
            additionalProperties: false
            required: [path]
            properties:
              path: { $ref: "#/$defs/nonEmptyString" }
          - type: object
            additionalProperties: false
            required: [path, mode]
            properties:
              path: { $ref: "#/$defs/nonEmptyString" }
              mode: { $ref: "#/$defs/nonEmptyString" }
          - type: object
            additionalProperties: false
            required: [path, owner, group]
            properties:
              path: { $ref: "#/$defs/nonEmptyString" }
              owner: { $ref: "#/$defs/nonEmptyString" }
              group: { $ref: "#/$defs/nonEmptyString" }

  variableContract:
    type: object
    additionalProperties: false
    required:
      - name
      - type
      - defaults
      - allowed_values
      - grading_overlay_targets
      - binding_targets
    properties:
      name: { $ref: "#/$defs/nonEmptyString" }
      type: { $ref: "#/$defs/varType" }
      defaults:
        type: object
        additionalProperties: false
        required: [student]
        properties:
          student: {}
      allowed_values:
        type: array
        minItems: 1
        items: {}
      grading_overlay_targets:
        type: array
        minItems: 1
        items: { $ref: "#/$defs/overlayTarget" }
      binding_targets:
        type: array
        items: { $ref: "#/$defs/binding" }
      bindings_mode: { $ref: "#/$defs/bindingMode" }

  precedenceLayer:
    type: string
    enum:
      - role_default
      - role_vars
      - play_vars
      - vars_files
      - inventory_vars
      - group_vars
      - host_vars
      - extra_vars

  phaseName:
    type: string
    enum: [baseline, mutation]

  precedenceScenario:
    type: object
    additionalProperties: false
    required: [name, variable, layers, expected_winner, bindings_to_verify]
    properties:
      name: { $ref: "#/$defs/nonEmptyString" }
      variable: { $ref: "#/$defs/nonEmptyString" }
      layers:
        type: array
        minItems: 2
        items: { $ref: "#/$defs/precedenceLayer" }
      expected_winner: { $ref: "#/$defs/precedenceLayer" }
      bindings_to_verify:
        type: array
        minItems: 1
        items: { type: integer, minimum: 0 }
      phase: { $ref: "#/$defs/phaseName" }

  nodeSelector:
    type: object
    additionalProperties: false
    properties:
      group: { $ref: "#/$defs/nonEmptyString" }
      host: { $ref: "#/$defs/nonEmptyString" }
    oneOf:
      - required: [group]
      - required: [host]

  packageContract:
    type: object
    additionalProperties: false
    required: [name, state, node_selector]
    properties:
      name: { $ref: "#/$defs/nonEmptyString" }
      state: { type: string, enum: [present, absent] }
      node_selector: { $ref: "#/$defs/nodeSelector" }
      weight: { type: number, minimum: 0.0, default: 1.0 }

  serviceContract:
    type: object
    additionalProperties: false
    required: [name, enabled, running, node_selector]
    properties:
      name: { $ref: "#/$defs/nonEmptyString" }
      enabled: { type: boolean }
      running: { type: boolean }
      node_selector: { $ref: "#/$defs/nodeSelector" }
      weight: { type: number, minimum: 0.0, default: 1.0 }

  portRef:
    oneOf:
      - type: integer
        minimum: 1
        maximum: 65535
      - type: object
        additionalProperties: false
        required: [var]
        properties:
          var: { $ref: "#/$defs/nonEmptyString" }

  firewallPort:
    type: object
    additionalProperties: false
    required: [port, protocol, zone]
    properties:
      port: { $ref: "#/$defs/portRef" }
      protocol: { type: string, enum: [tcp, udp] }
      zone: { $ref: "#/$defs/nonEmptyString" }

  firewallContract:
    type: object
    additionalProperties: false
    required: [open_ports, node_selector]
    properties:
      open_ports:
        type: array
        minItems: 1
        items: { $ref: "#/$defs/firewallPort" }
      node_selector: { $ref: "#/$defs/nodeSelector" }
      weight: { type: number, minimum: 0.0, default: 1.0 }

  fileContractItem:
    type: object
    additionalProperties: false
    required: [path, present]
    properties:
      path: { $ref: "#/$defs/nonEmptyString" }
      present: { type: boolean }
      mode: { $ref: "#/$defs/nonEmptyString" }
      owner: { $ref: "#/$defs/nonEmptyString" }
      group: { $ref: "#/$defs/nonEmptyString" }
      content_regex: { $ref: "#/$defs/nonEmptyString" }

  filesContract:
    type: object
    additionalProperties: false
    required: [items, node_selector]
    properties:
      items:
        type: array
        minItems: 1
        items: { $ref: "#/$defs/fileContractItem" }
      node_selector: { $ref: "#/$defs/nodeSelector" }
      weight: { type: number, minimum: 0.0, default: 1.0 }

  reachabilityExpectation:
    type: string
    enum: [reachable, not_reachable]

  reachabilityContract:
    type: object
    additionalProperties: false
    required: [from_host, to_host, protocol, port, expectation]
    properties:
      from_host: { $ref: "#/$defs/nonEmptyString" }
      to_host: { $ref: "#/$defs/nonEmptyString" }
      protocol: { type: string, enum: [tcp, udp] }
      port: { $ref: "#/$defs/portRef" }
      expectation: { $ref: "#/$defs/reachabilityExpectation" }
      weight: { type: number, minimum: 0.0, default: 1.0 }

  trigger:
    oneOf:
      - type: object
        additionalProperties: false
        required: [file_changed]
        properties:
          file_changed: { $ref: "#/$defs/nonEmptyString" }
      - type: object
        additionalProperties: false
        required: [template_changed]
        properties:
          template_changed: { $ref: "#/$defs/nonEmptyString" }
      - type: object
        additionalProperties: false
        required: [variable_changed]
        properties:
          variable_changed: { $ref: "#/$defs/nonEmptyString" }

  nonTrigger:
    oneOf:
      - type: object
        additionalProperties: false
        required: [noop_rerun]
        properties:
          noop_rerun: { type: boolean, const: true }
      - type: object
        additionalProperties: false
        required: [unrelated_file_changed]
        properties:
          unrelated_file_changed: { $ref: "#/$defs/nonEmptyString" }

  expectedRuns:
    type: string
    enum: [zero, at_least_once, exactly_once]

  handlerContract:
    type: object
    additionalProperties: false
    required:
      - handler_name
      - node_selector
      - handler_target
      - trigger_conditions
      - non_trigger_conditions
      - expected_runs
    properties:
      handler_name: { $ref: "#/$defs/nonEmptyString" }
      node_selector: { $ref: "#/$defs/nodeSelector" }
      handler_target:
        type: object
        additionalProperties: false
        required: [service, action]
        properties:
          service: { $ref: "#/$defs/nonEmptyString" }
          action: { type: string, enum: [restart, reload] }
      trigger_conditions:
        type: array
        minItems: 1
        items: { $ref: "#/$defs/trigger" }
      non_trigger_conditions:
        type: array
        items: { $ref: "#/$defs/nonTrigger" }
      expected_runs:
        type: object
        additionalProperties: false
        required: [baseline, mutation, idempotence]
        properties:
          baseline: { $ref: "#/$defs/expectedRuns" }
          mutation: { $ref: "#/$defs/expectedRuns" }
          idempotence: { $ref: "#/$defs/expectedRuns" }
      weight: { type: number, minimum: 0.0, default: 2.0 }

  idempotencePolicy:
    type: object
    additionalProperties: false
    properties:
      required: { type: boolean, default: true }
      allowed_changes:
        type: array
        items: { $ref: "#/$defs/nonEmptyString" }
      enforcement:
        type: object
        additionalProperties: false
        properties:
          require_changed_zero: { type: boolean, default: true }
          require_no_handlers: { type: boolean, default: true }

  vaultSpec:
    type: object
    additionalProperties: false
    required: [vaulted_vars_files, vaulted_variables, bindings_to_verify]
    properties:
      vault_ids:
        type: array
        items: { $ref: "#/$defs/nonEmptyString" }
      vaulted_vars_files:
        type: array
        minItems: 1
        items: { $ref: "#/$defs/nonEmptyString" }
      vaulted_variables:
        type: array
        minItems: 1
        items: { $ref: "#/$defs/nonEmptyString" }
      bindings_to_verify:
        type: array
        minItems: 1
        items: { type: integer, minimum: 0 }

  phaseOverlays:
    type: object
    additionalProperties: false
    properties:
      baseline:
        type: object
        additionalProperties: false
        properties:
          inventory_vars: { type: object, additionalProperties: true }
          group_vars:
            type: object
            additionalProperties: true
          host_vars:
            type: object
            additionalProperties: true
          extra_vars: { type: object, additionalProperties: true }
      mutation:
        type: object
        additionalProperties: false
        properties:
          inventory_vars: { type: object, additionalProperties: true }
          group_vars:
            type: object
            additionalProperties: true
          host_vars:
            type: object
            additionalProperties: true
          extra_vars: { type: object, additionalProperties: true }

type: object
additionalProperties: false
required:
  - assignment_id
  - assignment_version
  - spec_version
  - seed
  - provider
  - os
  - topology
  - entrypoints
  - variable_contracts
  - phase_overlays
  - idempotence
properties:
  assignment_id: { $ref: "#/$defs/nonEmptyString" }
  assignment_version: { $ref: "#/$defs/nonEmptyString" }
  spec_version: { type: string, const: "1.0" }
  seed: { type: integer }
  provider: { type: string, const: "libvirt" }
  os: { type: string, const: "almalinux9" }
  features: { $ref: "#/$defs/featureFlags" }

  topology: { $ref: "#/$defs/topology" }
  entrypoints: { $ref: "#/$defs/entrypoints" }

  variable_contracts:
    type: array
    minItems: 1
    items: { $ref: "#/$defs/variableContract" }

  precedence_scenarios:
    type: array
    items: { $ref: "#/$defs/precedenceScenario" }

  behavioral_contracts:
    type: object
    additionalProperties: false
    properties:
      packages:
        type: array
        items: { $ref: "#/$defs/packageContract" }
      services:
        type: array
        items: { $ref: "#/$defs/serviceContract" }
      firewall:
        type: array
        items: { $ref: "#/$defs/firewallContract" }
      files:
        type: array
        items: { $ref: "#/$defs/filesContract" }
      reachability:
        type: array
        items: { $ref: "#/$defs/reachabilityContract" }

  handler_contracts:
    type: array
    items: { $ref: "#/$defs/handlerContract" }

  idempotence: { $ref: "#/$defs/idempotencePolicy" }

  vault: { $ref: "#/$defs/vaultSpec" }

  phase_overlays: { $ref: "#/$defs/phaseOverlays" }
```

Notes on strictness:

* The schema is strict on structure but permissive on overlay values (additionalProperties: true under overlay maps) because overlay maps are inherently variable-keyed.
* `bindings_to_verify` indexes into the variable contract `binding_targets` list. This makes references stable without copying binding structures across sections.

---

## Reference example assignment spec

This example is small but exercises: multi-node, variable mutation, precedence scenario, firewall + service checks, handler checks, reachability. It avoids vault in v1 example.

Scenario: web node runs nginx that listens on `http_port` and includes a config line `listen {{ http_port }}`. Firewall must allow the port. App node runs a simple service (could be podman container or a systemd unit the students create) but for v1 grading we only check reachability to nginx from app to web to force inter-node network correctness.

Students are free to implement however they want as long as bindings pass.

```yaml
assignment_id: "hammer-nginx-port"
assignment_version: "2026.02"
spec_version: "1.0"
seed: 1337
provider: "libvirt"
os: "almalinux9"

features:
  vault: false
  selinux: false
  handlers: true
  reachability: true

topology:
  nodes:
    - name: "web1"
      groups: ["web"]
      resources:
        cpu: 2
        ram_mb: 2048
    - name: "app1"
      groups: ["app"]
      resources:
        cpu: 1
        ram_mb: 1024
  dependencies:
    - from_host: "app1"
      to_host: "web1"
      kind: "reachability"

entrypoints:
  playbook_path: "site.yml"
  required_roles: ["web"]
  required_files: ["site.yml"]

variable_contracts:
  - name: "http_port"
    type: "int"
    defaults:
      student: 8080
    allowed_values: [8080, 9090]
    grading_overlay_targets:
      - overlay_kind: "group_vars"
        target_name: "web"
      - overlay_kind: "extra_vars"
        target_name: "all"
    bindings_mode: "all"
    binding_targets:
      - type: "service_listen_port"
        weight: 1.0
        target:
          service: "nginx"
          protocol: "tcp"
          address: "0.0.0.0"
      - type: "firewall_port_open"
        weight: 1.0
        target:
          zone: "public"
          protocol: "tcp"
      - type: "template_contains"
        weight: 1.0
        target:
          path: "/etc/nginx/conf.d/hammer.conf"
          pattern: "listen {{ value }};"

  - name: "welcome_text"
    type: "string"
    defaults:
      student: "hello"
    allowed_values: ["hello", "bonjour"]
    grading_overlay_targets:
      - overlay_kind: "group_vars"
        target_name: "web"
    bindings_mode: "all"
    binding_targets:
      - type: "file_contains"
        weight: 1.0
        target:
          path: "/usr/share/nginx/html/index.html"
          pattern: "{{ value }}"

precedence_scenarios:
  - name: "extra_vars_overrides_group_vars_http_port"
    variable: "http_port"
    layers: ["group_vars", "extra_vars"]
    expected_winner: "extra_vars"
    bindings_to_verify: [0, 1, 2]
    phase: "mutation"

behavioral_contracts:
  packages:
    - name: "nginx"
      state: "present"
      node_selector:
        group: "web"
      weight: 1.0
  services:
    - name: "nginx"
      enabled: true
      running: true
      node_selector:
        group: "web"
      weight: 1.0
  firewall:
    - open_ports:
        - port: { var: "http_port" }
          protocol: "tcp"
          zone: "public"
      node_selector:
        group: "web"
      weight: 1.0
  files:
    - items:
        - path: "/etc/nginx/conf.d/hammer.conf"
          present: true
          mode: "0644"
          owner: "root"
          group: "root"
          content_regex: "listen"
        - path: "/usr/share/nginx/html/index.html"
          present: true
      node_selector:
        group: "web"
      weight: 1.0
  reachability:
    - from_host: "app1"
      to_host: "web1"
      protocol: "tcp"
      port: { var: "http_port" }
      expectation: "reachable"
      weight: 1.0

handler_contracts:
  - handler_name: "restart nginx"
    node_selector:
      group: "web"
    handler_target:
      service: "nginx"
      action: "restart"
    trigger_conditions:
      - template_changed: "/etc/nginx/conf.d/hammer.conf"
      - variable_changed: "http_port"
    non_trigger_conditions:
      - noop_rerun: true
      - unrelated_file_changed: "/etc/hosts"
    expected_runs:
      baseline: "at_least_once"
      mutation: "exactly_once"
      idempotence: "zero"
    weight: 2.0

idempotence:
  required: true
  allowed_changes: []
  enforcement:
    require_changed_zero: true
    require_no_handlers: true

phase_overlays:
  baseline:
    group_vars:
      web:
        http_port: 8080
        welcome_text: "hello"
    host_vars: {}
    inventory_vars: {}
    extra_vars: {}
  mutation:
    group_vars:
      web:
        http_port: 8080
        welcome_text: "bonjour"
    host_vars: {}
    inventory_vars: {}
    extra_vars:
      http_port: 9090
```

What this enforces:

* Baseline: nginx up, firewall open 8080, file contains listen 8080, index contains hello.
* Mutation: welcome text changes to bonjour (group_vars). http_port must become 9090 because extra_vars wins.
* Handler: expected to run exactly once in mutation converge due to config/var change; must not run in idempotence converge.
* Reachability: app1 can connect to web1:9090 in mutation.

---

## Generated artifact layout

This layout is what the lock should checksum and what the runner should write. Keeping it fixed makes debugging and reproducibility much easier.

Student bundle (output directory)

```text
student_bundle/
  README.md
  Vagrantfile
  inventory/
    hosts.yml
    group_vars/
      web.yml
      app.yml
    host_vars/
      web1.yml
      app1.yml
  site.yml
  roles/
    web/
      tasks/main.yml
      handlers/main.yml
      templates/
        hammer.conf.j2
  tests/
    test_contracts.py
    conftest.py
  tools/
    snapshot_local.py
```

Grading bundle

```text
grading_bundle/
  ansible.cfg
  inventory/
    hosts.yml
    group_vars/
      web.yml
      app.yml
    host_vars/
      web1.yml
      app1.yml
  overlays/
    baseline/
      group_vars/
      host_vars/
      inventory_vars.yml
      extra_vars.yml
    mutation/
      group_vars/
      host_vars/
      inventory_vars.yml
      extra_vars.yml
  snapshot_playbook/
    snapshot.yml
    templates/
      snapshot_host.json.j2
  tests/
    test_contracts.py
    conftest.py
    hidden/
      test_hidden_contracts.py
  runner/
    hammer_runner.py
```

Grading run output (produced by `hammer grade`)

```text
run_out/
  score.json
  lock.json
  logs/
    vagrant_up.log
    vagrant_status.log
  ansible/
    baseline/
      runner_artifacts/...
      stdout.txt
      stderr.txt
    mutation/
      runner_artifacts/...
    idempotence/
      runner_artifacts/...
  snapshots/
    baseline/web1.json
    baseline/app1.json
    mutation/web1.json
    mutation/app1.json
    idempotence/web1.json
    idempotence/app1.json
  pytest/
    baseline/
      junit.xml
      pytest.txt
    mutation/
      junit.xml
    idempotence/
      junit.xml
```

---

## Test generation mapping for the example

To keep v1 mechanical, each spec item maps to one or more generated tests. Example mapping:

* variable_contract http_port:

  * test_web1_listening_on_http_port (uses snapshot var + testinfra socket)
  * test_web1_firewall_allows_http_port (uses snapshot var + firewall check strategy)
  * test_hammer_conf_contains_listen (uses snapshot var + file contains)
* behavioral packages/services/files:

  * test_nginx_installed, test_nginx_running_enabled, test_file_modes
* reachability:

  * test_app1_can_connect_to_web1_port (runs on app1 host, connects to web1 IP and port from snapshot)
* handlers:

  * runner-event verification function (not a pytest test on target host) that asserts handler execution counts per phase
  * system-observable verification: compare nginx main pid start time or service ActiveEnterTimestamp changes between baseline and mutation, and no change between mutation and idempotence

For firewall checks on AlmaLinux 9, the least flaky v1 strategy is:

* Primary: reachability from app1 to web1:port must succeed.
* Secondary: on web1, check firewalld zone has port open using firewall-cmd (stable enough if pinned).
* If firewalld is not running but reachability is correct, decide policy. For v1, I would require firewalld running if firewall contracts exist.

---

## Minimal runner behavior (implementation blueprint)

This is not full code, but it is precise enough to implement directly.

Phase inputs:

* student_path
* grading_bundle paths (inventory root, overlays per phase, ansible.cfg)
* lock.json
* phase name

Phase converge steps (baseline/mutation/idempotence):

* vagrant up (first converge only) with deterministic Vagrantfile
* extract ssh config for inventory connection vars (or generate inventory using vagrant ssh-config output)
* run ansible-runner with:

  * ANSIBLE_CONFIG pointing to grading ansible.cfg
  * inventory pointing to grading inventory
  * extravars loaded from phase overlays extra_vars.yml
  * environment vars for vault if enabled

Snapshot steps (after each converge):

* run ansible-runner on snapshot_playbook/snapshot.yml
* write JSON per host to run_out/snapshots/<phase>/<host>.json

Verify steps:

* run pytest with environment variables:

  * HAMMER_PHASE
  * HAMMER_SNAPSHOT_DIR
  * HAMMER_INVENTORY (for host selection, not for values)
* run runner-event verifier that parses ansible-runner events for handler expectations and idempotence

Scoring:

* combine contract results with weights
* write score.json

---

