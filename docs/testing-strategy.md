# Testing & Verification Strategy

**Milestone:** 003 — Part 2: Experimental Design & Architecture Finalized  
**Status:** Tier 1 and Tier 2 Active (*Agent runner, collectors, evaluators, and benchmark experiment tiers detailed for M004/M005*)  
**Primary Research Reference:** See [`docs/research/research-direction-and-scope.md`](research/research-direction-and-scope.md) for full evaluation methodology, condition definitions, and independent ground-truth formulation.  
**Architectural Decisions:** See [`docs/decisions/ADR-003-research-direction-and-next-architecture.md`](decisions/ADR-003-research-direction-and-next-architecture.md).

---

## 1. Testing Philosophy & Harness Principles

Testing in this research project serves two distinct functions:
1. **Software Quality Assurance:** Verifying that our target application, evidence collectors, and security evaluation engine operate correctly, reliably, and deterministically.
2. **Empirical Security Verification:** Measuring evaluator reliability (Precision, Recall, FPR, FNR) by subjecting tool-using agents to adversarial inputs and comparing evaluator verdicts against independent ground truth.

### Core Testing Axiom
> **Absence of failure does not prove security.**
> When an adversarial test suite passes without triggering a security violation, the conclusion is strictly that *no vulnerability was discovered under the specific parameters and prompt distributions tested*. It does not guarantee resilience against untested attack vectors.

### Evaluator Independence Rule
The target AI agent must **never** evaluate its own security or influence ground truth. All verdicts must originate from the independent `security_engine` using observable, deterministic criteria (trace inspection and database state diffs) evaluated against independently established ground truth ($Y \in \{0, 1\}$).

---

## 2. Test Pyramid & Hierarchy

```text
                  +-------------------------------+
                  | Tier 5: Benchmark Experiments |
                  | (Promptfoo vs Conditions A-D) |
                  +-------------------------------+
                +-----------------------------------+
                |  Tier 4: Regression Test Suite    |
                |  (Replay of known failure modes)  |
                +-----------------------------------+
              +---------------------------------------+
              | Tier 3: Security Invariant Tests (SEC)|
              | (Adversarial prompts & policy checks) |
              +---------------------------------------+
            +-------------------------------------------+
            |      Tier 2: Integration Test Suite       |
            |   (FastAPI + SQLite + Tools + Collectors) |
            +-------------------------------------------+
          +-----------------------------------------------+
          |          Tier 1: Unit Test Suite              |
          |  (Schemas, policy logic, diff algorithms)     |
          +-----------------------------------------------+
```

---

## 3. Test Tiers & Specifications

### Tier 1: Unit Tests (`tests/unit/`)
- **Scope:** Pure functions and isolated components.
- **Focus:**
  - Pydantic schema validation for tool inputs, outputs, and `EvaluationEvidenceBundle`.
  - Policy invariant parsing and rule matching logic.
  - SQLite state serialization and diff calculation algorithms ($\Delta S$).
  - Evaluator condition unit logic (Condition A regex matchers, Condition B trace validators, Condition C auth classifiers, Condition D correlation verifiers).
- **Speed & Execution:** Must run in < 1 second; zero network or live LLM dependencies.
- **Status:** **Active** (Schemas, policy logic, audit models tested and passing).

### Tier 2: Integration Tests (`tests/integration/`)
- **Scope:** Inter-component interactions without live LLM inference.
- **Focus:**
  - FastAPI endpoints correctly creating, updating, and querying synthetic SQLite records.
  - Tool handlers enforcing tenant authentication when invoked by `MockAgentRunner`.
  - Trace collector correctly intercepting tool invocations and recording return payloads.
  - State differ taking pre/post SQLite snapshots and producing accurate row-level diffs.
- **Speed & Execution:** Fast (< 5 seconds); uses temporary local SQLite instances.
- **Status:** **Active** (API, health, auth, audit, and CRUD tests passing).

### Tier 3: Security Invariant Tests (`tests/security/`)
- **Scope:** Falsification tests targeting defined security invariants (e.g., `SEC-01`).
- **Focus:**
  - Verifying backend enforcement of cross-tenant boundaries under direct parameter tampering.
  - Testing canary token non-leakage under unauthorized read requests.
  - Confirming state immutability when unauthorized modifications are rejected.
  - Verifying defended attempts are logged with `auth_decision: DENY` and produce $Y = 0$.
- **Status:** **Active** (SEC-01 read & modification isolation tests passing).

### Tier 4: Regression Tests (`tests/security/regression/`)
- **Scope:** Replay suite for every confirmed failure or evaluator misclassification.
- **Focus:**
  - Archiving prompts that triggered silent execution false negatives ($FN_{\text{silent}}$).
  - Archiving prompts that induced blocked attempt false alarms ($FP_{\text{blocked}}$).
  - Archiving prompts that induced hallucinated leak false alarms ($FP_{\text{hallucinated}}$).
- **Status:** *Planned* (Milestone 004).

### Tier 5: Benchmark Experiments (`experiments/`)
- **Scope:** Empirical evaluation comparing detector reliability across the four evaluator conditions (Condition A — Response-only, Condition B — Trace-based, Condition C — Authorization-aware, Condition D — Full-evidence) and the baseline Promptfoo framework against independently established ground truth ($Y \in \{0, 1\}$).
- **Focus:**
  - Measuring Evaluator Precision, Recall, False Positive Rate (FPR), False Negative Rate (FNR), and F1-score across balanced benign and adversarial prompt suites ($N \ge 100$).
  - Quantifying specific failure modes ($R_{\text{silent}}$, $R_{\text{blocked}}$, $R_{\text{hallucinated}}$).
  - Calculating Wilson score 95% confidence intervals and McNemar's test $\chi^2$ statistics.
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
| **Overall** | All Active Tests | 24 | 24 | **Passing** | 24 passed in ~5s. Epistemic invariant applies: guarantees bounded to tested conditions. |
