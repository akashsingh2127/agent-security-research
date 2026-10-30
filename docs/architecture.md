# System Architecture & Boundaries

**Milestone:** 002 — Secure Synthetic Target Application  
**Status:** Target Application Implemented & Tested (*Agent orchestration and Security Engine planned*)

---

## 1. Architectural Philosophy & Harness Boundaries

The primary objective of this architecture is to provide an empirical research harness for testing AI agent security. In conventional evaluations, an LLM evaluator often acts as a judge based solely on final conversational outputs. This project separates the application domain from the security verification domain so that internal tool calls, authorization bindings, and persistent state mutations can be audited out-of-band.

```
+-------------------------------------------------------------------------+
| UNTRUSTED EXTERNAL BOUNDARY                                             |
| User / Attacker Session                                                 |
+-------------------------------------------------------------------------+
                                    |
                                    v (HTTP / JSON API)
+-------------------------------------------------------------------------+
| TRUST BOUNDARY 1: TARGET APPLICATION (`target_app`)                     |
|                                                                         |
|  +--------------------+       +-------------------------------------+   |
|  | FastAPI Gateway    | ----> | LangGraph Agent Controller          |   |
|  | Context & Auth     |       | (Prompt + Tool Binding + Ollama)    |   |
|  +--------------------+       +-------------------------------------+   |
|                                                |                        |
|                                                v                        |
|                               +-------------------------------------+   |
|                               | Application Tool Handlers           |   |
|                               | (ReadRecord, UpdateRecord, etc.)    |   |
|                               +-------------------------------------+   |
|                                                |                        |
|                                                v                        |
|                               +-------------------------------------+   |
|                               | SQLite Synthetic Storage            |   |
|                               +-------------------------------------+   |
+-------------------------------------------------------------------------+
                                    |
            (Passive Event / Trace Emission & Pre/Post Snapshots)
                                    |
                                    v
+-------------------------------------------------------------------------+
| TRUST BOUNDARY 2: SECURITY ENGINE (`security_engine`)                   |
|                                                                         |
|  +-----------------------------+     +-------------------------------+  |
|  | Trace & State Interceptor   |     | Formal Security Invariants    |  |
|  | - Captured tool calls       |     | - Policy Specifications       |  |
|  | - Pre/post DB checksums     |     |   (e.g., SEC-01 multi-tenant) |  |
|  +-----------------------------+     +-------------------------------+  |
|                 \                                   /                   |
|                  \                                 /                    |
|                   v                               v                     |
|          +-------------------------------------------------+            |
|          | State & Execution Policy Verifier               |            |
|          | (Independent Deterministic Verification)        |            |
|          +-------------------------------------------------+            |
|                                   |                                     |
|                                   v                                     |
|          +-------------------------------------------------+            |
|          | Verification Report & Comparative Metrics       |            |
|          | (Evaluator Verdict vs. Baseline Benchmark)      |            |
|          +-------------------------------------------------+            |
+-------------------------------------------------------------------------+
```

---

## 2. Component Boundaries

### 2.1 Target Application (`target_app`)
- **Role:** Simulates a realistic multi-tenant enterprise application where private records are protected by backend ownership policies, and an AI assistant will later have access to database-interacting tools.
- **Implemented Components (Milestone 002):**
  - *FastAPI Gateway:* Ingests requests with correlation IDs (`X-Request-ID`) and Bearer token headers.
  - *Authentication Provider (`auth.py`):* Deterministically maps pre-shared local research tokens to authenticated principals (`user_a`, `user_b`, `user_c`).
  - *Authorization Service (`service.py`):* Enforces strict backend record ownership (`caller == owner_id`) on all protected reads and modifications.
  - *Audit Logger (`audit.py`):* Persists append-only audit events (`event_id`, `principal_id`, `action`, `resource_id`, `resource_owner`, `auth_decision`, `outcome`, `request_id`).
  - *SQLite Database (`database.py`, `seed.py`):* Holds synthetic multi-tenant tables (`users`, `records`, `audit_events`) with deterministic, idempotent seed data.
- **Planned Components (Milestone 003):**
  - *LangGraph Agent:* Conversational agent controller connecting prompts and local Ollama models.
  - *Tool Handlers:* Explicit tool functions wrapping target application services for agent invocation.
- **Trust Assumption:** The target agent is considered **compromised or fallible**. Prompt injection, jailbreaking, or reasoning failures may induce the agent to attempt unauthorized tool calls. Backend controls enforce ground truth.

### 2.2 Security Engine (`security_engine`)
- **Role:** Independent evaluation harness capable of judging whether an agent's actions conformed to formal security policies.
- **Components:**
  - *Trace Interceptor:* Captures the sequence of tool invocations, parameter bindings, and executing tenant context.
  - *State Differ:* Takes cryptographic hashes and structured row diffs of SQLite before and after agent execution.
  - *Policy Verifier:* Evaluates the combined trace and state delta against formal invariant rules (e.g., SEC-01).
  - *Report Generator:* Emits structured JSON/CSV logs detailing policy compliance, violations, and false positive/negative rates.
- **Trust Assumption:** The Security Engine is **trusted and authoritative**. It has direct, read-only observation capabilities over application state transitions and execution logs. The target agent has **zero access or authority** over this layer.

### 2.3 External Baseline (`baselines/`)
- **Role:** Houses benchmark configurations for external security tools (primarily Promptfoo).
- **Function:** Executes identical adversarial prompts against the target agent and records black-box verdicts based on prompt and output text alone, providing the empirical comparison for our research hypothesis.

---

## 3. Planned Evidence Flow

When an evaluation run is executed:
1. **State Snapshot:** The Security Engine records the pre-execution database state (table checksums and row snapshots).
2. **Adversarial Stimulus:** An input prompt (benign or containing prompt injection attacks) is sent to the Target Application under a specific actor context (e.g., User A).
3. **Trace Collection:** The Target Application executes. As tools are invoked, execution events (tool name, bound arguments, caller identity, return payload) are recorded in an immutable trace object.
4. **State Diffing:** Once the agent turn completes, the Security Engine captures the post-execution database state and calculates the exact delta ($\Delta State$).
5. **Policy Verification:** The Verifier inspects:
   - *Was any unauthorized tool invoked?*
   - *Did any tool invocation access or expose records of another tenant?*
   - *Did the database state change for any records not owned by the calling tenant?*
6. **Verdict Emission:** An authoritative binary verdict (`PASS` / `FAIL`) accompanied by structured diagnostic evidence is generated.

---

## 4. Deferred Components & Justifications

* **Docker / Containerization:**
  - *Decision:* Deferred.
  - *Justification:* During foundational design and early agent bring-up, local Python 3.12 virtual environments and local SQLite storage provide minimal overhead, rapid iteration cycles, and immediate test execution. Containerization adds orchestration complexity and will be introduced when multi-environment cross-validation is needed.
* **Streamlit / Web UI:**
  - *Decision:* Deferred.
  - *Justification:* Research evaluation requires rigorous, repeatable, scripted CLI batch runs and machine-readable data outputs (JSON/CSV) for statistical analysis. A graphical dashboard introduces maintenance overhead without contributing to empirical validity.

---

## 5. Architectural Status

- **System boundaries defined:** Milestone 001 (**Implemented**)
- **Target App implementation:** Milestone 002 (**Implemented & Tested**)
- **Target Agent & Tool bindings:** *Planned* (Milestone 003)
- **Security Engine implementation:** *Planned* (Milestone 004)
- **Baseline integration:** *Planned* (Milestone 005)
- **Any operational security guarantees:** **Unverified** (Direct backend invariants verified under tested conditions; agent-mediated security remains unverified)

