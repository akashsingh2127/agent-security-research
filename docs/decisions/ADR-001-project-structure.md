# ADR-001: Separation of Target Application and Security Evaluation Engine

**Status:** Accepted  
**Date:** 2026-10-30  
**Deciders:** Senior Software Architect, Research Team  
**Milestone:** 001 — Foundation  

---

## 1. Context & Problem Statement

When evaluating the security of tool-using AI agents, the evaluation mechanism must determine whether an agent's execution violated system security invariants (such as multi-tenant isolation).

Common industry approaches typically take one of two flawed paths:
1. **Self-Evaluation:** The agent itself is prompted after execution to report whether it acted securely or followed instructions. This is untrustworthy due to model hallucination, sycophancy, or direct adversarial manipulation.
2. **Black-Box Output Grading:** An external grader evaluates only the natural language output returned to the user (e.g., using LLM-as-a-judge or regex heuristics in prompt-level benchmarks like Promptfoo). This fails to detect cases where the agent executed an unauthorized tool call (e.g., mutating database state or fetching unauthorized data) but masked or omitted the action in its final verbal response.

To investigate whether verifying observed authorization decisions and application state transitions provides higher reliability, we must establish a clear structural boundary between the system under test and the evaluation engine.

---

## 2. Decision

We decide to separate the repository source code and runtime boundaries into two distinct packages:
1. **`target_app/`:** Contains the target system under evaluation, including the FastAPI interface, LangGraph agent orchestration, tool implementations, and SQLite data access.
2. **`security_engine/`:** Contains the independent security verification harness, including execution trace listeners, database state diffing utilities, formal policy specifications, and verdict reporting.

Furthermore, we establish the following architectural invariants:
- **Zero Evaluator Authority for the Agent:** The agent under test has no visibility into or control over `security_engine`.
- **Out-of-Band Observation:** The `security_engine` observes the target application via structured trace events and pre/post state snapshots, remaining decoupled from internal agent reasoning loops.
- **Independent Baseline Interface:** External baseline tools (such as Promptfoo) reside in `baselines/` and interact with `target_app` through standard external endpoints, enabling direct, fair comparison with `security_engine`.

---

## 3. Consequences

### Positive Consequences
- **Integrity of Evaluation:** An exploited or misbehaving agent cannot alter its own evaluation logs, suppress state diffs, or corrupt verdict calculations.
- **Research Rigor:** Enables direct, controlled comparison between state-and-trace-verified evaluation (`security_engine`) and prompt-only black-box evaluation (`baselines/promptfoo`).
- **Modular Maintainability:** The target application architecture can be updated (e.g., swapping agent prompts or models) without rewriting verification logic, and vice versa.

### Negative Consequences / Trade-offs
- **Instrumentation Overhead:** Requires explicit hooks or event emitters in `target_app` to expose structured execution traces and database transaction boundaries to `security_engine`.
- **Coordination Complexity:** Test harnesses must orchestrate starting the application, resetting the database, triggering the agent, capturing state, and collecting traces across package boundaries.

---

## 4. Alternatives Considered

### Alternative A: Monolithic Single-Package Application
- *Description:* Place evaluation logic and security checks inside the agent's application code or prompt context.
- *Rejection Rationale:* Blurs trust boundaries. An adversarial prompt that manipulates the agent's context window could directly manipulate the validation code or trick the agent into reporting false compliance.

### Alternative B: Pure Black-Box Testing Without State Access
- *Description:* Treat `target_app` as a complete black box and evaluate only HTTP responses using external tools like Promptfoo.
- *Rejection Rationale:* Directly contradicts our research hypothesis. Black-box evaluations cannot observe internal tool calls or verify whether unauthorized database mutations occurred if the agent does not verbalize them.

