# CODE_REVIEW.md — Remaining Items

**Date:** 2026-02-07
**Scope:** Gap analysis of CODE_REVIEW.md against current codebase

Of the 33 action items in CODE_REVIEW.md, **29 are fully implemented** and **4 remain open** (3 not done, 1 partial). An additional 3 items are partially done and could benefit from further work.

---

## Not Implemented

### 1. UX-3: Disk Space Pre-Flight Check (Priority: Medium)

**Original issue:** Each VM uses 2-10GB. Grading 30 students with 2-node specs requires 120-600GB. No pre-flight disk check, no cleanup utility.

**Why it matters:** Users hit cryptic libvirt/Vagrant errors when disk fills mid-provision. A simple check before `hammer build` or `hammer grade` would prevent wasted time.

**Suggested approach:**
- Add `shutil.disk_usage()` check in `prerequisites.py`
- Estimate required space from node count and resources
- Warn (not block) if available space is below threshold

**Effort:** Low

---

### 2. UX-8: Batch/Parallel Grading (Priority: Medium)

**Original issue:** `hammer grade` runs one student at a time. Grading a class of 30 for PE4 takes 7+ hours.

**Why it matters:** Instructors grading a full class face long wait times. Parallel grading would dramatically improve throughput.

**Suggested approach:**
- Add `hammer grade-batch --submissions-dir DIR` command
- Use `concurrent.futures.ProcessPoolExecutor` with configurable parallelism
- Each student gets isolated working directory
- Aggregate results into a CSV/JSON summary

**Effort:** High

---

### 3. TEST-6: Property-Based Testing with Hypothesis (Priority: Low)

**Original issue:** Spec validation is ideal for property-based testing — generate random specs and verify valid specs build, invalid specs raise errors, and determinism holds.

**Why it matters:** Would catch edge cases in validation logic that hand-written tests miss. Nice-to-have for robustness.

**Suggested approach:**
- Add `hypothesis` to dev dependencies
- Write strategies for generating valid/invalid spec fragments
- Key properties: determinism (same seed = same output), roundtrip (valid spec -> build -> success)

**Effort:** Medium

---

## Partially Implemented (Could Be Improved)

### 4. UX-2: Cross-Platform Support/Guidance (Priority: Low)

**Current state:** QUICKSTART.md and CONTRIBUTING.md exist, but no explicit macOS/Windows guidance.

**Gap:** Educational settings often have instructors on macOS. Docs should clarify that HAMMER requires Linux with KVM, and suggest alternatives (e.g., running inside a Linux VM, or using a CI runner).

**Effort:** Low (documentation only)

---

### 5. UX-4: VM Failure Recovery (Priority: Low)

**Current state:** TROUBLESHOOTING.md covers some recovery procedures. No automatic retry logic.

**Gap:** Retry logic for transient failures (network timeouts during `vagrant up`) would improve reliability. Currently users must manually `vagrant destroy -f` and restart.

**Effort:** Medium

---

### 6. TEST-3: Runner Error Path Tests (Priority: Low)

**Current state:** `test_reboot.py` has good mock coverage. `ansible.py` and `pytest_runner.py` error paths have minimal test coverage.

**Gap:** Subprocess failure, timeout, and missing-executable paths in `runner/ansible.py` and `runner/pytest_runner.py` lack dedicated mock tests.

**Effort:** Low

---

### 7. SEC-5: Predictable Temp File in HTTP Tests (Priority: Low)

**Current state:** `test_http.py.j2` still writes to `/tmp/hammer_http_response`. Acceptable risk given single-VM test isolation.

**Gap:** Could use `tempfile.mkstemp()` or a unique suffix for defense in depth.

**Effort:** Low

---

## Summary

| # | Item | Priority | Effort | Status |
|---|------|----------|--------|--------|
| 1 | UX-3: Disk space check | Medium | Low | Not done |
| 2 | UX-8: Batch grading | Medium | High | Not done |
| 3 | TEST-6: Property-based testing | Low | Medium | Not done |
| 4 | UX-2: Cross-platform docs | Low | Low | Partial |
| 5 | UX-4: VM failure recovery | Low | Medium | Partial |
| 6 | TEST-3: Runner error path tests | Low | Low | Partial |
| 7 | SEC-5: Predictable temp file | Low | Low | Partial |

**Overall CODE_REVIEW.md completion: ~88% (29/33 items fully done)**
