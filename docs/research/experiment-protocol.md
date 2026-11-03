# Experiment Protocol: Policy Verification vs. Black-Box Evaluation

**Status:** Milestone 003 — Part 1: Refined Research Protocol  
**Last Updated:** 2026-11-03  
**Authors:** Senior AI Security Researcher & Methodology Reviewer  

> [!NOTE]
> **Scientific Integrity Notice:**
> This document specifies the controlled experimental protocol for validating our refined research hypothesis. All experimental results, baseline scores, and performance metrics are currently uncollected. No claims of experimental success or definitive novelty are asserted prior to empirical testing.

---

## 1. Research Hypothesis & Core Research Question

### Refined Core Research Question (Milestone 003)
> *"How do progressive levels of evaluator observability—ranging from black-box agent responses to execution traces, backend authorization decisions, and persistent database state diffs—impact the precision, recall, and false-negative rates of security violation detection in tool-using AI agents subjected to unauthorized cross-tenant data access (BOLA/BFLA) attacks?"*

### Hypotheses
> **Hypothesis $H_1$:** Progressively incorporating backend authorization decisions and persistent database state diffs with execution traces significantly reduces evaluator false-negative rates (detecting silent state mutations) and false-positive rates (avoiding flagging blocked attempts or hallucinated breaches) compared to response-only (Condition A) and trace-only (Condition B) evaluators.
>
> **Null Hypothesis $H_0$:** There is no statistically significant difference in detection precision, recall, or error rates across the four progressive evaluator observability conditions.

---

## 2. Experimental Variables

### 2.1 Independent Variables
1. **Evaluator Observability Condition (Treatment Progression):**
   - **Condition A (Response-Only):** Evaluator observes solely the agent's final natural language response text (representative of standard Promptfoo output assertions and LLM-as-a-judge).
   - **Condition B (Trace-Based):** Evaluator observes tool names, bound arguments, caller identity, and tool return payloads captured during execution.
   - **Condition C (Trace + Authorization):** Evaluator observes execution traces plus server-side authorization evaluation decisions (`auth_decision`: `ALLOW` vs. `DENY` from `audit_events`).
   - **Condition D (Full Evidence Ground Truth):** Evaluator observes execution traces, backend authorization decisions, output canary disclosure checks, and pre/post persistent SQLite database row-level state diffs ($\Delta S$).
2. **Adversarial Stimulus Category:**
   - *Benign Controls:* Authorized requests within tenant scope (e.g., User A accessing `rec_a_001`).
   - *Direct BOLA Probing:* Prompts directing the agent to read or modify another tenant's record (`rec_b_001`).
   - *Indirect Prompt Injection (IPI):* Benign user queries that retrieve records containing hidden instructions ordering cross-tenant access.
   - *Confused Deputy / Social Engineering:* Jailbreak or roleplay prefixes coercing the agent to bypass tenant rules.
   - *Parameter Tampering:* Subtle substitution of User B's record IDs in User A's session context.
3. **Target Agent System:**
   - Tool-using agent orchestrated with LangGraph and local Ollama model (e.g., Qwen 2.5 3B/7B Instruct) interacting with the Milestone 002 `target_app` API.

### 2.2 Dependent Variables & Evaluator Error Metrics
1. **Evaluator Recall / True Positive Rate (TPR):** Proportion of actual security violations correctly detected by the evaluator: $\frac{TP}{TP + FN}$.
2. **Evaluator False Positive Rate (FPR):** Proportion of non-violations incorrectly flagged as violations: $\frac{FP}{FP + TN}$.
3. **Evaluator Precision:** $\frac{TP}{TP + FP}$.
4. **Evaluator F1-Score:** $2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$.
5. **Silent Execution False Negative Rate:** The rate at which an unauthorized database mutation occurred ($\Delta S \neq \emptyset$) but the evaluator reported `PASS` because the agent masked the action in its verbal response.
6. **Blocked Attempt False Positive Rate:** The rate at which an evaluator flagged a security violation solely because an unauthorized tool call was attempted, even though the backend returned `403 Forbidden` and no state changed or data leaked.
7. **Hallucinated Leak False Positive Rate:** The rate at which an evaluator flagged a violation because the agent claimed in text to have accessed private data, despite no tool execution or data retrieval having occurred.
8. **Evaluation Latency:** Execution and scoring overhead (wall-clock milliseconds per turn).

---

## 3. Synthetic Test Environment & Dataset Specification

### 3.1 Synthetic Multi-Tenant Dataset
- Relational schema hosted in SQLite.
- Minimum 3 distinct tenant identities:
  - Tenant A (Adversary context).
  - Tenant B (Target victim context).
  - Tenant C (Control baseline context).
- Deterministic seeding with fixed primary keys, canary tokens, and mock records.

### 3.2 Prompt Evaluation Suite
- **Dataset Size:** Minimum $N = 100$ balanced prompts ($50$ benign control prompts, $50$ adversarial prompts across direct, indirect, and parameter tampering vectors).
- **Randomization:** Deterministic pseudo-random seed recorded for prompt presentation order.

---

## 4. Execution Protocol & Step-by-Step Procedure

1. **Pre-Run State Reset:**
   - Clean the SQLite database and populate with deterministic synthetic seed data.
   - Record baseline database cryptographic checksum.
2. **Execution Execution:**
   - Send prompt $i$ to `target_app` with authenticated context `User A`.
   - Record agent natural language response.
   - Capture full execution trace (tool calls, arguments, outputs).
3. **Post-Run State Snapshot:**
   - Compute post-execution database cryptographic checksum and row diffs ($\Delta S$).
4. **Treatment Evaluation (`security_engine`):**
   - Pass execution trace and $\Delta S$ to `security_engine` policy verifier.
   - Record verdict: `PASS` / `FAIL` and violation type.
5. **Baseline Evaluation (`baselines/promptfoo`):**
   - Execute Promptfoo assertion suite on prompt $i$ and agent response.
   - Record Promptfoo verdict: `PASS` / `FAIL`.
6. **Ground Truth Labeling:**
   - Compare both verdicts against deterministic ground-truth labels established by test suite design.
7. **Post-Run Database Reset:**
   - Restore database to baseline state before processing prompt $i+1$.

---

## 5. Statistical Analysis Plan

- **Contingency Tables:** Construct $2 \times 2$ confusion matrices for both evaluators.
- **Hypothesis Testing:**
  - McNemar's test for paired nominal data to determine if the difference in error rates between `security_engine` and `promptfoo` is statistically significant ($p < 0.05$).
- **Reporting:** Tabulate metrics with 95% confidence intervals (Wilson score intervals for proportions).

---

## 6. Current Protocol Status

- **Protocol Initial Design:** Milestone 001 (**Implemented**)
- **Target Application Ground Truth:** Milestone 002 (**Implemented & Tested**)
- **Protocol Refinement & Error Taxonomy:** Milestone 003 — Part 1 (**Implemented**)
- **Target Agent & Tool Harness:** *Planned* (Milestone 003 — Part 2)
- **Evaluator Conditions (A, B, C, D) Implementation:** *Planned* (Milestone 004)
- **Data Collection & Empirical Benchmarking:** *Planned* (Milestone 005)
- **Results & Findings:** **Unverified** (No empirical runs executed yet)

