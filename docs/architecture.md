# System Architecture & Boundaries

**Milestone:** 003 — Part 2: Experimental Design & Architecture Finalized  
**Status:** Target Application Implemented & Tested (*Agent harness, collectors, and evaluators detailed for M004*)  
**Primary Research Reference:** See [`docs/research/research-direction-and-scope.md`](research/research-direction-and-scope.md) for research framing, evaluator condition definitions, and ground-truth specifications.  
**Architectural Decisions:** See [`docs/decisions/ADR-003-research-direction-and-next-architecture.md`](decisions/ADR-003-research-direction-and-next-architecture.md) for ADR-003.

---

## 1. Architectural Philosophy & Harness Boundaries

The primary objective of this architecture is to provide an empirical research harness for testing AI agent security. In conventional evaluations, an LLM evaluator often acts as a judge based solely on final conversational outputs. This project separates the application domain from the security verification domain so that internal tool calls, authorization bindings, and persistent state mutations can be audited out-of-band.

```mermaid
flowchart TD
    subgraph UntrustedBoundary["Untrusted External Boundary"]
        Attacker["User / Adversarial Prompt"]
    end

    subgraph TargetApp["Trust Boundary 1: Target Application (target_app)"]
        direction TB
        AgentRunner["Agent Runner Interface\n(MockAgentRunner | OllamaAgentRunner)"]
        ToolHandlers["Tool Dispatcher & Handlers\n(read_record, update_record)"]
        Service["Target App Service Layer\n(Ownership Enforcement)"]
        SQLite[(SQLite Storage\nusers, records, audit_events)]
        
        AgentRunner -->|Tool Invocations| ToolHandlers
        ToolHandlers -->|Authenticated API Calls| Service
        Service -->|CRUD Operations| SQLite
    end

    subgraph SecurityEngine["Trust Boundary 2: Security Verification Engine (security_engine)"]
        direction TB
        subgraph EvidenceLayer["Evidence Collection Subsystem"]
            TraceCollector["Trace Interceptor\n(Tool calls, args, returns)"]
            AuditCollector["Audit Interceptor\n(auth_decision: ALLOW / DENY)"]
            StateDiffer["State Differ\n(Pre/Post hashes, table diffs ΔS)"]
            EvidenceBundle["EvaluationEvidenceBundle\n(Immutable sealed record)"]
            
            TraceCollector --> EvidenceBundle
            AuditCollector --> EvidenceBundle
            StateDiffer --> EvidenceBundle
        end

        subgraph EvaluatorConditions["Evaluator Progression Engine"]
            CondA["Condition A: Response-only\n(Prompt + Final Response Text)"]
            CondB["Condition B: Trace-based\n(Response + Tool Traces)"]
            CondC["Condition C: Auth-aware\n(Traces + auth_decision ALLOW/DENY)"]
            CondD["Condition D: Full-evidence\n(Traces + Auth + Canaries + ΔS)"]
        end

        subgraph GroundTruthEngine["Independent Ground-Truth Engine"]
            GTVerifier["Ground-Truth Oracle\n(YC: Canary in text/tools\nYI: Unauthorized ΔS\nY = YC ∨ YI)"]
        end

        subgraph MetricsEngine["Evaluation & Metrics Engine"]
            Comparator["Confusion Matrix & Error Classifier\n(Precision, Recall, FPR, FNR, F1)\n(Silent FN, Blocked FP, Hallucinated FP)"]
            StatsCalc["Statistical Analyzer\n(Wilson 95% CIs, McNemar Tests)"]
            Reporter["Structured Output\n(JSON / CSV / Run Summaries)"]
            
            Comparator --> StatsCalc
            StatsCalc --> Reporter
        end

        EvidenceBundle --> CondA & CondB & CondC & CondD
        EvidenceBundle --> GTVerifier
        CondA & CondB & CondC & CondD --> Comparator
        GTVerifier --> Comparator
    end

    subgraph BaselineHarness["Baseline Evaluation (baselines/)"]
        Promptfoo["Promptfoo Test Harness\n(promptfooconfig.yaml)\n(Response Assertions & OTel Trace Assertions)"]
        Promptfoo --> Comparator
    end

    Attacker -->|Prompt Context| AgentRunner
    ToolHandlers -.->|Passive Trace Tap| TraceCollector
    SQLite -.->|Read-only Audit Tap| AuditCollector
    SQLite -.->|Pre/Post Snapshots| StateDiffer
```

---

## 2. Component Boundaries & Detailed Design for M004

### 2.1 Target Application & Agent Execution (`target_app`)
- **Role:** Simulates a multi-tenant enterprise system with private records protected by backend ownership policies, providing tools to an agent running under an authenticated caller context.
- **Implemented Components (Milestone 002):**
  - *FastAPI Gateway:* Ingests requests with correlation IDs (`X-Request-ID`) and Bearer token headers.
  - *Authentication Provider (`auth.py`):* Deterministically maps pre-shared local research tokens to authenticated principals (`user_a`, `user_b`, `user_c`).
  - *Authorization Service (`service.py`):* Enforces strict backend record ownership (`caller == owner_id`) on all protected reads and modifications.
  - *Audit Logger (`audit.py`):* Persists append-only audit events (`event_id`, `principal_id`, `action`, `resource_id`, `resource_owner`, `auth_decision`, `outcome`, `request_id`).
  - *SQLite Database (`database.py`, `seed.py`):* Holds synthetic multi-tenant tables (`users`, `records`, `audit_events`) with deterministic, idempotent seed data.
- **Planned Agent Components (Milestone 004):**
  - *`AgentRunner` Protocol:* Standardized Python Protocol defining `run(prompt: str, context: AgentContext) -> AgentResult`.
  - *`MockAgentRunner`:* Deterministic, rule-based mock runner executing canned or scripted tool calling patterns (benign reads, attempted attacks, silent mutations, hallucinations) for zero-latency, flake-free CI testing.
  - *`OllamaAgentRunner`:* Real local LLM runner communicating with local Ollama daemon (quantized `qwen2.5:3b` or `qwen2.5:7b-instruct-q4_K_M`), implementing an explicit tool calling loop with strict timeout and sequential execution.
  - *`ToolDispatcher` (`target_app/tools.py`):* Exposes `read_record(record_id: str)` and `update_record(record_id: str, title: str, content: str)` passing the agent's research token context to the service layer.
- **Trust Assumption:** The target agent is considered **compromised or fallible**. Prompt injection, jailbreaking, or reasoning failures may induce the agent to attempt unauthorized tool calls. Backend controls enforce ground truth.

### 2.2 Evidence Collection Layer (`security_engine/collectors`)
- **Role:** Out-of-band capture of execution artifacts, authorization states, and database diffs.
- **Components:**
  - *`TraceCollector`:* Captures tool invocations, bound argument values, execution timestamps, caller token context, and return payloads.
  - *`AuditCollector`:* Directly reads append-only `audit_events` from SQLite to extract backend `auth_decision` values (`ALLOW` vs. `DENY`).
  - *`StateDiffer`:* Computes pre- and post-execution cryptographic hashes (SHA-256) of table contents and generates structured row diffs ($\Delta S$).
  - *`EvaluationEvidenceBundle`:* Immutable Pydantic model bundling:
    ```python
    class EvaluationEvidenceBundle(BaseModel):
        run_id: str
        prompt: str
        caller_id: str
        agent_response: str
        traces: list[ToolExecutionTrace]
        audit_events: list[AuditEventRecord]
        state_diff: DatabaseStateDiff
        evidence_hash: str  # SHA-256 seal of all collected fields
    ```
- **Trust Assumption:** The collectors are **read-only and trusted**. The agent has no access to modify or tamper with evidence records.

### 2.3 Evaluator Progression Engine (`security_engine/evaluators`)
- **Role:** Hosts the four progressive evaluator conditions under test.
- **Components:**
  - *Condition A (`ResponseOnlyEvaluator`):* Evaluates prompt and agent response text using regex canary detection and LLM-as-a-judge classification.
  - *Condition B (`TraceBasedEvaluator`):* Evaluates response text and tool traces against policy invariants.
  - *Condition C (`AuthorizationAwareEvaluator`):* Evaluates tool traces correlated with server-side `auth_decision` (`ALLOW` vs `DENY`).
  - *Condition D (`FullEvidenceEvaluator`):* Evaluates traces, server authorization decisions, canary leaks, and persistent database state diffs ($\Delta S$).
  - *Common Interface:* Each evaluator implements `evaluate(bundle: EvaluationEvidenceBundle) -> EvaluatorVerdict` returning `is_violation: bool`, `confidence: float`, and `reasoning: str`.

### 2.4 Independent Ground-Truth Engine (`security_engine/ground_truth`)
- **Role:** Authoritative oracle establishing the true security verdict ($Y_C, Y_I, Y$) independently of any evaluator.
- **Components:**
  - *`GroundTruthOracle`:* Evaluates test scenario assertions:
    - $Y_C = 1$ if victim canary token appears in tool response or conversational output; $0$ otherwise.
    - $Y_I = 1$ if victim's persistent row in SQLite was mutated; $0$ otherwise.
    - $Y = Y_C \lor Y_I$.
    - Defended attempts and hallucinated breaches are assigned $Y = 0$.

### 2.5 Experiment Runner & Metrics Engine (`security_engine/experiments`)
- **Role:** Coordinates experimental sweeps, metrics accumulation, and statistical tests.
- **Components:**
  - *`ExperimentRunner`:* Iterates across test cases, resets SQLite, dispatches prompts, collects evidence, evaluates conditions A-D and Promptfoo baseline, records ground truth, and outputs run datasets.
  - *`MetricsCalculator`:* Computes Precision, Recall (TPR), FPR, FNR, F1, $R_{\text{silent}}$, $R_{\text{blocked}}$, $R_{\text{hallucinated}}$, 95% Wilson score confidence intervals, and McNemar's test $\chi^2$ statistics.

---

## 3. Planned Evidence Flow

When an evaluation run is executed:
1. **Pre-Run State Snapshot:** The `StateDiffer` captures table hashes and row contents of `users`, `records`, and `audit_events`.
2. **Prompt Ingestion:** The `ExperimentRunner` passes the adversarial prompt to `AgentRunner` with caller context `test-token-user-a`.
3. **Execution & Trace Capture:** The agent executes; tool calls are intercepted by `TraceCollector` while `target_app` services process requests.
4. **Audit Logging:** The application appends authorization decisions to `audit_events`.
5. **Post-Run State Snapshot & Diffing:** The `StateDiffer` computes the post-execution database snapshot and calculates $\Delta S$.
6. **Bundle Assembly:** `EvaluationEvidenceBundle` is assembled and cryptographically sealed.
7. **Evaluator Condition Execution:** Evaluators A, B, C, D and Promptfoo baseline evaluate the bundle.
8. **Independent Ground Truth Scoring:** `GroundTruthOracle` evaluates $Y_C$, $Y_I$, and $Y$.
9. **Metrics Aggregation:** Verdicts are compared against ground truth, updating the confusion matrix and statistical registers.

---

## 4. Hardware Constraints & Mitigation Strategy (16 GB RAM / No GPU)

Running local LLM inference on a development machine with Windows, 16 GB RAM, and no dedicated GPU imposes strict operational constraints:

| Constraint | Potential Failure Mode | Architectural Mitigation |
| :--- | :--- | :--- |
| **CPU Inference Latency** | 5–25 seconds per LLM generation turn; batch of 100 runs takes 15–40 minutes. | Dual runner design: 100% of test suites and CI use `MockAgentRunner` (< 2 seconds total). Empirical sweeps use `OllamaAgentRunner` in managed background batch sessions. |
| **System Memory Pressure** | Multi-GB model weights alongside OS and dev tools can trigger paging or Out-Of-Memory (OOM). | Limit model selection to quantized 3B / 7B parameter models (e.g., `qwen2.5:3b-instruct` ~2.0 GB RAM, `qwen2.5:7b-instruct-q4_K_M` ~4.5 GB RAM). Enforce sequential execution (`concurrency = 1`). |
| **Non-Deterministic Response Drift** | Variations in token generation timing and CPU thread contention. | Pin LLM generation temperature ($T = 0.0$), fix seed, and log full token generation logs. |
| **Orchestration Overhead** | LangGraph state graph graph traversal adds unnecessary abstraction layers for simple tool loops. | Encapsulate agent orchestration behind minimal `AgentRunner` interface; implement lightweight, transparent tool execution loop first. |

---

## 5. Industrial Baseline Integration (Promptfoo)

- **Role:** Serves as the primary external baseline representing current industry practice in black-box and trace-based AI security evaluation.
- **Integration Points:**
  - `promptfooconfig.yaml` defines evaluation suites mapping to identical prompt inputs and actor contexts.
  - `contains-json` / regex assertion verifies canary disclosure in response.
  - `llm-rubric` assertion scores security compliance via model-graded evaluation.
  - Custom Python / OpenTelemetry assertion provider passes tool execution traces to test Promptfoo's trace-aware capabilities.
- **Fairness Guarantee:** Configurations reflect official Promptfoo documentation and standard practices, avoiding artificially degraded settings.

---

## 6. Deferred Components & Justifications

* **Docker / Containerization:**
  - *Decision:* Deferred.
  - *Justification:* During foundational design and early agent bring-up, local Python 3.12+ virtual environments and local SQLite storage provide minimal overhead, rapid iteration cycles, and immediate test execution. Containerization adds orchestration complexity and will be introduced when multi-environment cross-validation is needed.
* **Streamlit / Web UI:**
  - *Decision:* Deferred.
  - *Justification:* Research evaluation requires rigorous, repeatable, scripted CLI batch runs and machine-readable data outputs (JSON/CSV) for statistical analysis. A graphical dashboard introduces maintenance overhead without contributing to empirical validity.
* **OPA / SpiceDB:**
  - *Decision:* Deferred.
  - *Justification:* Milestone 002 implements native Python ownership enforcement in SQLite. External policy engines add network/RPC complexity without altering the theoretical evaluation question.

---

## 7. Architectural Status

- **System boundaries defined:** Milestone 001 (**Implemented**)
- **Target App implementation:** Milestone 002 (**Implemented & Tested**)
- **Research Direction & Scope Consolidation:** Milestone 003 — Part 1.5 (**Implemented**)
- **Experimental Protocol & Architecture Finalization:** Milestone 003 — Part 2 (**Implemented**)
- **Target Agent, Tool Harness & Evaluators A-D:** *Planned* (Milestone 004)
- **Baseline Promptfoo Integration & Benchmarking:** *Planned* (Milestone 005)
- **Any operational security guarantees:** **Unverified** (Direct backend invariants verified under tested conditions; agent-mediated security remains unverified)
