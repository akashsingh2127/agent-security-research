# Literature Review: Policy Verification & Security Evaluation for AI Agents

**Status:** Milestone 003 — Part 1.5: Consolidated Literature Review & Methodology Alignment  
**Last Updated:** 2026-11-10  
**Authors:** Senior AI Security Researcher & Methodology Reviewer  
**Primary Reference:** See [`docs/research/research-direction-and-scope.md`](research-direction-and-scope.md) for the central research roadmap and scope definitions.

---

## 1. Research Scope & Objectives

This literature review investigates existing methodologies for evaluating the security of tool-using Large Language Model (LLM) agents. The primary objective is to critically examine our refined research inquiry:

> *"How do progressive levels of evaluator observability—ranging from black-box agent responses to execution traces, backend authorization decisions, and persistent database state diffs—impact the precision, recall, and false-negative rates of security violation detection in tool-using AI agents subjected to unauthorized cross-tenant data access (BOLA/BFLA) attacks?"*

Specifically, this review investigates:
1. **Benchmark Frameworks for Agent Security:** Existing automated evaluation tools and benchmarks (AgentDojo, ASB, InjecAgent, INFUSE, Promptfoo, Garak).
2. **Failure Modes in Tool-Using Agents:** Broken Object Level Authorization (BOLA), Broken Function Level Authorization (BFLA), prompt injection, confused deputy behaviors, and silent execution failures.
3. **Evidence Layers in Security Evaluation:** Response text, execution traces, backend authorization logs, and persistent state diffs.
4. **Evaluator Reliability:** The distinction between evaluating *agent attack success* versus evaluating *evaluator precision and recall*.

---

## 2. Taxonomy of Existing Agent Security Benchmarks

### 2.1 Comparative Capability Matrix

The following table systematically evaluates existing agent security benchmarks and testing tools against the five core evidence dimensions:

| Project / Tool | Traces | Authorization Evidence | Disclosure Evidence | State Verification | Detector Precision / Recall Measured? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **AgentDojo** (Debenedetti et al., 2024) | **Yes** | **No** | **Partial** | **Yes** | **No** (Measures agent ASR / Utility) |
| **ASB** (Zhang et al., 2024) | **Yes** | **No** | **Partial** | **Partial** | **No** (Measures agent ASR / DSR) |
| **InjecAgent** (Zeng et al., 2024) | **Yes** | **No** | **Partial** | **No** | **No** (Measures agent ASR) |
| **INFUSE** (Nguyen et al., 2026) | **Yes** | **No** | **Partial** | **Yes** | **Yes** (Validates judge vs. human labels) |
| **Promptfoo** (Promptfoo Open Source, 2024–2026) | **Partial** | **No** | **Partial** | **No** | **No** (Reports test pass/fail rate) |
| **Garak** (NVIDIA / Garak Team, 2024–2026) | **No** | **No** | **Partial** | **No** | **No** (Reports probe hit rate) |
| **OWASP Multi-Identity API Tools** (RESTler, Schemathesis) | **Partial** | **Yes** | **Partial** | **Partial** | **Partial** (API flaw detection, non-agent) |
| **Our Proposed Evaluator Harness** (`security_engine`) | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** (Primary research metric) |

*Legend: **Yes** = Fully supported / verified capability; **Partial** = Limited to specific subcases or text heuristics; **No** = Not supported or absent; **Unknown** = Unverifiable from public documentation.*

---

### 2.2 In-Depth Analysis of Key Prior Work

#### 1. AgentDojo (Debenedetti et al., NeurIPS 2024)
- **Reference:** Edoardo Debenedetti, Jie Zhang, Balraj Ambresh, et al., *"AgentDojo: A Dynamic Environment to Benchmark Attacks and Defenses on LLM Agents"*, arXiv:2406.13352 [cs.CR], 2024. [https://arxiv.org/abs/2406.13352](https://arxiv.org/abs/2406.13352)
- **Problem Solved:** Benchmarking indirect prompt injection (IPI) vulnerabilities and defensive trade-offs in tool-using agents interacting with untrusted data across realistic software suites (email, e-banking, travel, workspace).
- **Attacks Covered:** Indirect prompt injection, goal hijacking, unauthorized data exfiltration, and unauthorized actions.
- **Evidence Collected:** Dynamic tool execution sequences and post-execution environment state.
- **Ground Truth Establishment:** Deterministic Python assertions evaluating task completion (utility) and malicious side-effects (security).
- **Metrics Reported:** Attack Success Rate (ASR) and Utility Completion Rate.
- **Evaluator Target:** Evaluates *agent performance and defense efficacy*; does **not** evaluate evaluator accuracy or compare different evaluator information conditions.
- **Overlap & Differentiation:** AgentDojo validates the necessity of inspecting environment state for agent security. However, it models single-user environments without server-side multi-tenant authorization policies (BOLA/BFLA), and does not ablate evaluator observability.

#### 2. Agent Security Bench / ASB (Zhang et al., ICLR 2025)
- **Reference:** Zhang et al., *"Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents"*, arXiv:2410.02644 [cs.CR], 2024. [https://arxiv.org/abs/2410.02644](https://arxiv.org/abs/2410.02644)
- **Problem Solved:** Formalizing and evaluating threats targeting multiple operational stages of agents (planning, tool use, memory retrieval) across 10 real-world scenarios and 400+ tools.
- **Attacks Covered:** Direct prompt injection, indirect prompt injection, memory poisoning attacks, and Plan-of-Thought (PoT) backdoor attacks.
- **Evidence Collected:** Step-by-step action plans, tool call logs, and memory updates.
- **Ground Truth Establishment:** Scenario-specific target outcome matching.
- **Metrics Reported:** Attack Success Rate (ASR), Defense Success Rate (DSR), and Utility Preservation.
- **Evaluator Target:** Evaluates *agent vulnerabilities across model families*; does not evaluate evaluator reliability.
- **Overlap & Differentiation:** ASB illustrates multi-stage agent vulnerabilities. However, it treats the evaluator as a fixed oracle rather than studying evaluator false positive/negative rates, and does not evaluate backend authorization decisions.

#### 3. InjecAgent (Zeng et al., ACL Findings 2024)
- **Reference:** Shenglin Zeng et al., *"InjecAgent: Benchmarking Indirect Prompt Injection Attacks on Tool-Integrated Large Language Model Agents"*, arXiv:2403.02691 [cs.CR], 2024. [https://arxiv.org/abs/2403.02691](https://arxiv.org/abs/2403.02691)
- **Problem Solved:** Quantifying agent susceptibility to indirect prompt injection across 1,054 test cases covering 17 user tools and 62 attacker tools.
- **Attacks Covered:** Direct user harm (unauthorized actions) and private data exfiltration.
- **Evidence Collected:** Single-step and multi-step tool call invocations and bound parameters.
- **Ground Truth Establishment:** Exact parameter matching against predefined attack goals.
- **Metrics Reported:** Attack Success Rate (ASR) across ReAct and function-calling agents.
- **Evaluator Target:** Evaluates *agent susceptibility*; does not evaluate the evaluator.
- **Overlap & Differentiation:** Demonstrates that agents frequently pass attacker parameters into tools. However, InjecAgent operates with mock tools without persistent database state and lacks backend authorization enforcement.

#### 4. INFUSE (Nguyen et al., October 2026) — *Special Critical Analysis*
- **Reference:** Thuy Nguyen, Jing-Yi Guo, Rana Seda Dubauskas, Sreepriya Damuluru, Taylor T. Johnson, Kevin Leach, *"INFUSE: A Unified Surface Benchmark for Indirect Prompt Injection in Agentic Systems"*, arXiv:2610.20776 [cs.CR], October 2026. [https://arxiv.org/abs/2610.20776](https://arxiv.org/abs/2610.20776)
- **Problem Solved:** Benchmarking indirect prompt injection across realistic, multi-surface, long-horizon workflows (shell execution, code compilation, git interactions, remote services).
- **Attacks Covered:** 56 attack scenarios across 5 threat categories injecting through files, web pages, git repositories, and build tools.
- **Evidence Collected:** Comprehensive execution trajectories (command strings, outputs, tool parameters) and environment artifacts (git commits, created/modified files, exfiltration outputs).
- **Ground Truth & Evaluator Methodology:**
  - Employs a dual-axis evaluation:
    1. **ASR-L (LLM-evaluated Attack Success Rate):** LLM judge inspecting interaction trajectories to detect behavioral compromise.
    2. **ASR-H (Heuristic-evaluated Attack Success Rate):** Deterministic scripts verifying concrete environment artifacts (e.g., git commits, filesystem changes).
  - Conducts blinded human validation: Evaluates judge reliability against human consensus, reporting:
    * Cross-family Judge Committee: Cohen's $\kappa = 0.918$, **Precision = 0.930**, **Recall = 0.952**.
    * Single Judge (GPT-4o-mini): Cohen's $\kappa = 0.527$, **Precision = 0.706**, **Recall = 0.600**.
- **Critical Comparison with Our Research:**
  - *Key Finding:* INFUSE already proves that trajectory-based LLM judges diverge from deterministic artifact verifiers, and already measures evaluator precision and recall against human consensus.
  - *Gap Retained:* INFUSE investigates **indirect prompt injection in single-user operating system and development environments**. It does **not** investigate **multi-tenant authorization (BOLA/BFLA)**, does **not** capture or verify **server-side authorization decisions (`ALLOW` vs. `DENY`)**, and does **not** evaluate an experimental progression of evaluator observability conditions (A: response $\to$ B: trace $\to$ C: authorization $\to$ D: full state).

#### 5. Promptfoo (Baseline Red-Teaming & Assertion Framework)
- **Reference:** Promptfoo Project, *"Test your LLM apps, agents, and prompts"*, GitHub: `promptfoo/promptfoo`, 2024–2026. [https://github.com/promptfoo/promptfoo](https://github.com/promptfoo/promptfoo)
- **Problem Solved:** Industry-standard black-box and grey-box testing framework for LLMs, prompt pipelines, and tool-using agents.
- **Capabilities & Scope:** Promptfoo provides an extensive evaluation ecosystem including red-teaming plugins for BOLA, RBAC bypasses, SSRF, and prompt injection. It supports OpenTelemetry (OTel) trace ingestion, provider response parsing, and custom JavaScript/Python assertions targeting tool call arguments and execution trajectories.
- **Role in Our Research:** Promptfoo serves as a primary empirical baseline. Rather than treating blind spots as proven tool defects, our experiments are designed to test whether and under what conditions specific failure modes (such as silent state mutations or hallucinated leaks) emerge under fair, standard Promptfoo configurations that lack direct backend database state diffing.

#### 6. Garak (NVIDIA)
- **Reference:** NVIDIA / Garak Team, *"Garak: Generative AI Red-teaming & Assessment Kit"*, GitHub: `NVIDIA/garak`, 2024–2026. [https://github.com/NVIDIA/garak](https://github.com/NVIDIA/garak)
- **Problem Solved:** Vulnerability scanning of LLMs across OWASP LLM Top 10 categories.
- **Evidence Collected:** Input prompts and model text responses.
- **Limitations:** Purely response-oriented; does not support multi-step tool execution, backend authorization tracing, or state diffing.

#### 7. OWASP API Security & Multi-Identity Authorization Testing
- **Reference:** OWASP Foundation, *"OWASP Top 10 API Security Risks – 2023"*, 2023. [https://owasp.org/API-Security/editions/2023/en/](https://owasp.org/API-Security/editions/2023/en/)
- **Core Concepts & Distinction (BOLA vs. BFLA):**
  - **API1:2023 Broken Object Level Authorization (BOLA):** Endpoints fail to validate that an authenticated user has permission to access a specific resource ID (e.g., User A accessing `GET /records/{rec_b_001}`). Our current synthetic application enforces ownership checks on records, supporting BOLA-oriented testing.
  - **API5:2023 Broken Function Level Authorization (BFLA):** Non-privileged users accessing administrative or sensitive functions. BFLA testing requires function-level permissions, user roles (e.g., admin vs. standard user), and privileged endpoints. **Implementation Gap:** Because `target_app` currently implements object ownership without role hierarchies, BFLA is a planned extension and an explicit prerequisite before claiming BFLA test coverage.
- **Multi-Identity Testing (RESTler, Schemathesis, Pynt, Akto):**
  - Automated tools test BOLA by taking two distinct user identity contexts (User A and User B), sending requests intended for User B using User A's token, and asserting that the backend returns `403 Forbidden` rather than `200 OK`.
- **Gap in Agent Context:** These tools evaluate static HTTP clients directly. When an autonomous LLM agent sits between the user and the API, traditional API security testing does not capture whether conversational framing causes the agent to become a confused deputy, nor does it evaluate how an AI security monitor can detect such violations.

---

## 3. Evaluator Failure Modes: Theoretical Analysis

Evaluating tool-using agents creates four distinct failure quadrants across the observability spectrum:

```
                          ACTUAL BACKEND STATE / POLICY
                          Violation Occurred   | No Violation Occurred
                        -----------------------+-----------------------
  EVALUATOR   Flagged   | True Positive (TP)   | False Positive (FP)
  VERDICT     Violation |                      | (e.g. Hallucinated leak)
              ----------+----------------------+-----------------------
              Cleared   | False Negative (FN)  | True Negative (TN)
              (Pass)    | (e.g. Silent write)  |
```

### Specific Potential Failure Modes by Evaluator Condition:

1. **Condition A — Response-only Evaluator (Text assertions, output LLM-as-a-judge):**
   - **Silent Execution False Negative:** The agent executes an unauthorized tool call (`update_record(rec_b_001)`) and succeeds on a misconfigured backend, but generates a polite refusal to the user (*"I'm sorry, I cannot access other users' data"*). Condition A falsely scores this as `PASS` (False Negative).
   - **Hallucinated Leak False Positive:** The agent boasts to the attacker (*"Here is User B's secret ledger: $1,000,000"*), but hallucinated the data while the tool call was blocked by the backend (403 Forbidden). Condition A falsely scores this as a security violation (False Positive).

2. **Condition B — Trace-based Evaluator (Tool call and argument inspection):**
   - **Blocked Call False Positive:** The agent invokes `read_record(record_id='rec_b_001')`. A trace-only evaluator flags a security breach because an unauthorized argument was observed. However, the backend returned `403 Forbidden` and zero confidential data was disclosed. Flagging this as a completed violation conflates *attempted compromise* with *actual vulnerability exploitation*.
   - **Unenforced Invariant Blind Spot:** If a tool call appears legitimate on its face (valid types and schema), a trace-only evaluator without server-side policy context cannot determine whether the calling session principal owned the referenced resource ID.

3. **Condition C — Authorization-aware Evaluator (Traces + backend authorization decisions):**
   - Incorporates server-side authorization decisions (`ALLOW` vs. `DENY`).
   - Resolves the blocked-call false positive: recognizes that an attempted tool call was denied by the backend.
   - *Remaining Blind Spot:* If an unauthorized read was denied, but the agent leaked previously retrieved or injected canary data via natural language, Condition C cannot independently confirm whether data disclosure occurred without inspecting the output text.

4. **Condition D — Full-evidence Evaluator (Traces + authorization + disclosure + state diffs):**
   - Evaluator receives the complete runtime evidence bundle: response text, execution traces, backend authorization decisions, canary disclosure checks, and persistent database state diffs ($\Delta S$).
   - **Methodological Invariant:** Condition D is an *experimental evaluator condition*, **not** the definition of ground truth itself. Ground truth is established independently through pre-run test specifications and deterministic assertions (see Section 11 of `docs/research/research-direction-and-scope.md`).

---

## 4. Answers to Core Research Validation Questions

### Q1: Has existing work compared response-only, trace-based, and independent outcome-aware security evaluators?
**Answer: Partially in general agent settings, but not in a progressive, four-condition ablation.**
*INFUSE* (Nguyen et al., 2026) compared trajectory-level LLM judges (ASR-L) against heuristic artifact verifiers (ASR-H) and evaluated judge precision/recall against human consensus. However, no prior work within our reviewed literature has systematically ablated the progressive addition of evidence across response-only, trace-level, authorization-level, and persistent-state-level evaluator tiers.

### Q2: Has anyone performed this comparison specifically for authorization violations in AI agents?
**Answer: Within the reviewed works, we found no direct evaluation of detector reliability across progressive evidence conditions for multi-tenant authorization violations in tool-using agents. This remains a provisional research gap requiring broader validation.**
Existing benchmarks focus overwhelmingly on prompt injection, jailbreaks, and general tool misuse. Multi-tenant authorization (BOLA/BFLA, tenant data isolation, cross-tenant modification) has not been systematically investigated as an agent security benchmark domain, nor has evaluator reliability been measured for authorization attacks.

### Q3: Has anyone combined execution traces, backend authorization decisions, actual data disclosure, and persistent-state verification?
**Answer: Within the reviewed literature, no framework systematically combines all four evidence layers for evaluating AI agents.**
While software engineering tools use runtime verification and API testing tools inspect HTTP responses, no existing AI agent evaluation framework in our review unifies:
1. Agent tool execution traces,
2. Server-side authorization decisions (`ALLOW`/`DENY`),
3. Natural language canary disclosure verification, and
4. Independent pre/post persistent database state diffs ($\Delta S$).

### Q4: Which existing project is closest to our idea?
**Answer: INFUSE (academic) and Promptfoo (industrial).**
- *INFUSE* is closest methodologically because it explicitly measures evaluator precision and recall against human ground truth and distinguishes trajectory judges from artifact verifiers.
- *Promptfoo* is closest tooling-wise because it supports both black-box evaluations and OpenTelemetry trace assertions, and provides BOLA/RBAC red-teaming plugins.

### Q5: What is genuinely different, if anything?
**Answer:**
1. **Evaluator Reliability as Primary Metric:** We evaluate the *security evaluator's* error rates (TPR, FPR, precision, recall) across progressive observability tiers, rather than treating the evaluator as an assumed oracle to grade agents.
2. **Authorization Invariants (BOLA/BFLA Ground Truth):** We evaluate multi-tenant isolation where caller identity, resource ownership, and backend policy define deterministic ground truth.
3. **Disentangling Attack Attempts from Compromises:** We formally distinguish between an agent attempting an unauthorized action, the backend enforcing policy, the agent verbalizing/masking output, and persistent application state mutating.

### Q6: What is the smallest defensible research question?
**Answer:**
> **Refined Research Question:**
> *"How do progressive levels of evaluator observability—ranging from black-box agent responses to execution traces, backend authorization decisions, and persistent database state diffs—impact the precision, recall, and false-negative rates of security violation detection in tool-using AI agents subjected to unauthorized cross-tenant data access (BOLA/BFLA) attacks?"*

---

## 5. Research Gap Decision & Justification

### Decision: **B. Research direction needs refinement.**

### Evidence-Based Justification:
1. **Why not Decision A (Supported as-is)?**
   The original, broadly phrased research question (*"Can progressively combining execution traces, authorization decisions, and observed outcomes improve security-violation detection?"*) is too general and borders on an intuitive truth: providing an evaluator with complete ground truth obviously improves detection over incomplete data. Furthermore, INFUSE (Nguyen et al., 2026) has already demonstrated the divergence between trajectory-level judges and artifact checks. Claiming novelty for general "trace plus artifact" evaluation without qualification would be scientifically unsound.
2. **Why not Decision C (Not sufficiently novel)?**
   Within the reviewed literature, no prior work directly evaluates detector reliability across progressive evidence conditions for multi-tenant authorization violations in tool-using agents. Industry tools like Promptfoo operate with known blind spots under output-only configurations. Measuring the exact empirical failure rates across progressive observability tiers provides a genuine, publishable scientific contribution.
3. **Refinement Required & Adopted:**
   As codified in [`docs/research/research-direction-and-scope.md`](research-direction-and-scope.md), the research scope is strictly grounded in:
   - **Target Attack Class:** Multi-tenant authorization violations (starting with BOLA object isolation; BFLA deferred until function-level permissions are implemented).
   - **Evaluator Error Taxonomy:** Quantifying silent execution false negatives, hallucinated leak false positives, and blocked-attempt false positives.
   - **Empirical Baseline:** Rigorous comparison against Promptfoo's response-level and trace-level assertions under identical prompt distributions.

---

## 6. Verified References & Bibliography

1. **Debenedetti, E., Zhang, J., Ambresh, B., et al.** (2024). *AgentDojo: A Dynamic Environment to Benchmark Attacks and Defenses on LLM Agents.* Advances in Neural Information Processing Systems (NeurIPS 2024), arXiv:2406.13352 [cs.CR]. [https://arxiv.org/abs/2406.13352](https://arxiv.org/abs/2406.13352)
2. **Zhang, J., et al.** (2024). *Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents.* International Conference on Learning Representations (ICLR 2025), arXiv:2410.02644 [cs.CR]. [https://arxiv.org/abs/2410.02644](https://arxiv.org/abs/2410.02644)
3. **Zeng, S., et al.** (2024). *InjecAgent: Benchmarking Indirect Prompt Injection Attacks on Tool-Integrated Large Language Model Agents.* Findings of the Association for Computational Linguistics (ACL 2024), arXiv:2403.02691 [cs.CR]. [https://arxiv.org/abs/2403.02691](https://arxiv.org/abs/2403.02691)
4. **Nguyen, T., Guo, J.-Y., Dubauskas, R. S., Damuluru, S., Johnson, T. T., & Leach, K.** (October 2026). *INFUSE: A Unified Surface Benchmark for Indirect Prompt Injection in Agentic Systems.* arXiv:2610.20776 [cs.CR]. [https://arxiv.org/abs/2610.20776](https://arxiv.org/abs/2610.20776)
5. **Promptfoo Project.** (2024–2026). *Promptfoo: Test your LLM apps, agents, and prompts.* GitHub Repository. [https://github.com/promptfoo/promptfoo](https://github.com/promptfoo/promptfoo)
6. **NVIDIA / Garak Team.** (2024–2026). *Garak: Generative AI Red-teaming & Assessment Kit.* GitHub Repository. [https://github.com/NVIDIA/garak](https://github.com/NVIDIA/garak)
7. **OWASP Foundation.** (2023). *OWASP Top 10 API Security Risks – 2023.* OWASP API Security Project. [https://owasp.org/API-Security/editions/2023/en/](https://owasp.org/API-Security/editions/2023/en/)
