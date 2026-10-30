# Testing & Verification Strategy

**Milestone:** 002 — Secure Synthetic Target Application  
**Status:** Tier 1 and Tier 2 Active (*Agent and benchmark tiers planned*)

---

## 1. Testing Philosophy & Harness Principles

Testing in this research project serves two distinct functions:
1. **Software Quality Assurance:** Verifying that our target application and security evaluation engine operate correctly, reliably, and deterministically.
2. **Empirical Security Verification:** Falsifying security claims by subjecting tool-using agents to adversarial inputs and measuring policy conformance.

### Core Testing Axiom
> **Absence of failure does not prove security.**
> When an adversarial test suite passes without triggering a security violation, the conclusion is strictly that *no vulnerability was discovered under the specific parameters and prompt distributions tested*. It does not guarantee resilience against untested attack vectors.

### Evaluator Independence Rule
The target AI agent must **never** evaluate its own security. All verdicts must originate from the independent `security_engine` using observable, deterministic criteria (trace inspection and database state diffs).

---

## 2. Test Pyramid & Hierarchy

```text
                  +-------------------------------+
                  | Tier 5: Benchmark Experiments |
                  | (Promptfoo vs Security Engine)|
                  +-------------------------------+
                +-----------------------------------+
                |  Tier 4: Regression Test Suite    |
                |  (Replay of known attack vectors) |
                +-----------------------------------+
              +---------------------------------------+
              | Tier 3: Security Invariant Tests (SEC)|
              | (Adversarial prompts & policy checks) |
              +---------------------------------------+
            +-------------------------------------------+
            |      Tier 2: Integration Test Suite       |
            |   (FastAPI + SQLite + Tools in isolation) |
            +-------------------------------------------+
          +-----------------------------------------------+
          |          Tier 1: Unit Test Suite              |
          |  (Pydantic schemas, policy parsing, diff logic)|
          +-----------------------------------------------+
```

---

## 3. Test Tiers & Specifications

### Tier 1: Unit Tests (`tests/unit/`)
- **Scope:** Pure functions and isolated components.
- **Focus:**
  - Pydantic schema validation for tool inputs and outputs.
  - Policy invariant parsing and rule matching logic.
  - SQLite state serialization and diff calculation algorithms.
- **Speed & Execution:** Must run in < 1 second; zero network or LLM dependencies.
- **Status:** *Planned* (Milestone 002/003).

### Tier 2: Integration Tests (`tests/integration/`)
- **Scope:** Inter-component interactions without live LLM inference.
- **Focus:**
  - FastAPI endpoints correctly creating, updating, and querying synthetic SQLite records.
  - Tool handlers enforcing tenant authentication when invoked by mock callers.
  - Security engine interceptor correctly capturing mock traces and computing state hashes.
- **Speed & Execution:** Fast (< 5 seconds); uses in-memory or temporary SQLite instances.
- **Status:** *Planned* (Milestone 002).

### Tier 3: Security Invariant Tests (`tests/security/`)
- **Scope:** Falsification tests targeting defined security invariants (e.g., `SEC-01`).
- **Focus:**
  - Executing synthetic attacks (direct prompt injection, roleplay overrides, parameter tampering) against the target agent.
  - Verifying that the Security Engine detects any unauthorized read or modification of User B's records.
- **Status:** *Planned* (Milestone 003).

### Tier 4: Regression Tests (`tests/security/regression/`)
- **Scope:** Replay suite for every confirmed failure or bypass.
- **Focus:**
  - Whenever an adversarial prompt successfully bypasses defenses or exposes an evaluator blind spot, it is archived as a deterministic regression test.
- **Status:** *Planned* (Milestone 004).

### Tier 5: Benchmark Experiments (`experiments/`)
- **Scope:** Empirical evaluation comparing our Security Engine against external baselines (e.g., Promptfoo).
- **Focus:**
  - Measuring false positive rate, false negative rate, and detection latency across balanced suites of benign and malicious prompts.
- **Status:** *Planned* (Milestone 005).

---

## 4. Test Configuration & Tooling

Automated tests are managed via `pytest` configured in `pyproject.toml`:
- `pytest -m unit`: Run fast unit tests.
- `pytest -m integration`: Run application and tool integration tests.
- `pytest -m security`: Run security property invariant tests.
- `pytest -m experiment`: Run benchmark evaluation runs.

---

## 5. Current Verification Status

| Tier | Category | Current Count | Pass Count | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Unit | 12 | 12 | **Passing** | Policy checks, Pydantic schemas, and audit model tests. |
| **Tier 2** | Integration | 12 | 12 | **Passing** | Health, CRUD, auth rejection, 404/422 handling, test isolation. |
| **Tier 3** | Security Invariants | 4 | 4 | **Passing** | SEC-01 read & modification isolation, state immutability, canary nondisclosure. |
| **Tier 4** | Regression | 0 | 0 | *Planned* | Post-exploit regression replay suite (M004). |
| **Tier 5** | Experiments | 0 | 0 | *Planned* | Controlled prompt evaluation against Promptfoo (M005). |
| **Overall** | All Active Tests | 24 | 24 | **Passing** | 24 passed in 1.23s. Epistemic invariant applies: guarantees bounded to tested conditions. |

