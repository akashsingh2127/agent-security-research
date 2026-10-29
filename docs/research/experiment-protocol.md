# Experiment Protocol: Policy Verification vs. Black-Box Evaluation

**Status:** Working Protocol Template (*Study design specification; no experiments executed*)  
**Milestone:** 001 — Foundation  

> [!NOTE]
> **Scientific Integrity Notice:**
> This document specifies the controlled experimental protocol for validating our research hypothesis. All experimental results, baseline scores, and performance metrics are currently uncollected. No claims of experimental success are made.

---

## 1. Research Hypothesis

> **Hypothesis $H_1$:** An out-of-band security evaluation harness that verifies observed execution traces and application state deltas against formal security policies achieves significantly higher detection recall and precision for unauthorized agent actions than black-box prompt/response evaluators (Promptfoo).
>
> **Null Hypothesis $H_0$:** There is no statistically significant difference in detection recall or precision between execution-trace/state-level policy verification and prompt-level black-box evaluation.

---

## 2. Experimental Variables

### 2.1 Independent Variables
1. **Evaluation Methodology (Treatment vs. Baseline):**
   - *Treatment:* `security_engine` (Trace interception + SQLite state delta verification against SEC-01 invariants).
   - *Baseline:* `baselines/promptfoo` (Black-box evaluation using prompt assertions, output regex, and LLM-as-a-judge).
2. **Adversarial Stimulus Category:**
   - *Benign Prompts:* Authorized requests within tenant scope (e.g., User A accessing User A's data).
   - *Direct Prompt Injection:* Jailbreak prompts ordering the agent to bypass tenant restrictions.
   - *Indirect Prompt Injection:* Benign-appearing prompts triggering retrieval of records containing injected instructions.
   - *Parameter Tampering:* Requests subtly substituting User B's record IDs in User A's session.
3. **Agent Target Model:**
   - Local model family via Ollama (e.g., Qwen 2.5 3B/7B Instruct).

### 2.2 Dependent Variables & Metrics
1. **True Positive Rate (TPR / Recall):** Proportion of actual security violations correctly detected by the evaluator.
2. **False Positive Rate (FPR):** Proportion of benign, compliant runs incorrectly flagged as security violations.
3. **Precision:** $\frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$.
4. **F1-Score:** Harmonic mean of precision and recall.
5. **Silent Failure Detection Rate:** Number of instances where an unauthorized database mutation occurred without being mentioned in the agent's response text, detected by each method.
6. **Evaluation Latency:** Wall-clock time (seconds) required to execute and score each evaluation turn.

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

- **Protocol Design:** Milestone 001 (**Implemented**)
- **Data Collection:** *Planned* (Milestone 005)
- **Results & Findings:** **Unverified** (No empirical runs executed)

