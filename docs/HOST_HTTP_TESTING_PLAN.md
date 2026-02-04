# Host HTTP Testing Plan

## Current State

The `HttpEndpointContract` tests HTTP endpoints **from inside VMs** using testinfra:
- Runs `curl` from one VM to test another VM's webserver
- Uses `node_selector` to specify which VM runs the test

## Gap

No way to test HTTP endpoints **from the host machine** to VMs via forwarded ports.

Use cases:
- Verify a student's web app is accessible via port forwarding
- Test that nginx on VM port 80 is reachable via host port 8888
- Validate that the web application works end-to-end from external perspective

## Proposed Solution

### Option A: HostHttpContract (New Contract Type)

Add a new contract type that runs tests from the grading host rather than from VMs.

```yaml
behavioral_contracts:
  host_http_endpoints:
    - url: "http://localhost:8888/api/health"
      method: GET
      expected_status: 200
      response_contains: "healthy"
      target_node: "server0"  # For documentation, maps to forwarded port
      weight: 2.0
```

**Implementation:**
1. Add `HostHttpEndpointContract` to spec.py
2. Generate separate test file that doesn't use testinfra fixtures
3. Run these tests from the host using `requests` library
4. Execute after VM-internal tests

### Option B: Extend HttpEndpointContract with `from: host`

Add a `from` field to existing contract:

```yaml
behavioral_contracts:
  http_endpoints:
    - url: "http://localhost:8888/"
      from: host  # NEW: run from host instead of VM
      expected_status: 200
```

**Pros:** Simpler schema
**Cons:** Mixes two different test execution models

### Option C: Post-Phase Hooks

Add a `host_tests` section to phase overlays:

```yaml
phase_overlays:
  mutation:
    host_tests:
      - type: http
        url: "http://localhost:8888/"
        expected_status: 200
```

## Recommendation

**Option A** is cleanest - keeps VM tests and host tests clearly separated.

## Implementation Steps

1. Add `HostHttpEndpointContract` to `spec.py`
2. Add `host_http_endpoints` to `BehavioralContracts`
3. Create new test generator for host tests
4. Create `test_host_http.py.j2` template (uses `requests` not testinfra)
5. Update runner to execute host tests after VM tests
6. Add validation for forwarded_ports alignment

## Alternative: Out-of-Band Testing

If host HTTP testing is rare, could handle with:
- Manual verification step in grading
- Separate script run after HAMMER grading
- Documentation only (no automated testing)

## Priority

Medium - only needed when port forwarding + external access verification is required.
