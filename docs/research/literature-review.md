# Literature Review: Policy Verification & Security Evaluation for AI Agents

**Status:** Working Research Template (*Initial structure; unpopulated literature survey*)  
**Milestone:** 001 — Foundation  

> [!NOTE]
> **Scientific Integrity Notice:**
> This document is a foundational template. Literature findings, citations, and comparative gaps will be populated during the research phase. No literature claims, novelty assertions, or experimental results are fabricated.

---

## 1. Research Scope & Objectives

This literature review investigates existing methodologies for evaluating the security of tool-using Large Language Model (LLM) agents. Specifically, it surveys:
1. **Benchmark Frameworks for Agent Security:** Existing automated evaluation tools and benchmarks (e.g., Promptfoo, InjecAgent, AgentBench, etc.).
2. **Failure Modes in Tool-Using Agents:** Direct prompt injection, indirect prompt injection via retrieved content, parameter tampering, and confused deputy vulnerabilities.
3. **Execution Trace & Policy Verification:** Techniques from formal methods, runtime verification, and distributed systems applied to AI agent execution traces and persistent state transitions.
4. **Evaluator Reliability & Gaps:** Limitations of black-box evaluation, LLM-as-a-judge approaches, and prompt-only grading heuristics.

---

## 2. Taxonomy of Existing Agent Security Benchmarks

*(To be populated with systematic review findings)*

| Benchmark / Tool | Target Modality | Evaluation Mechanism | State Inspection? | Trace Inspection? | Key Limitations Identified |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Promptfoo** | LLM / Prompts / Agents | Black-box assertions, LLM-as-a-judge, regex matching | No (Black-box) | Partial (Plugin-dependent) | Misses silent state mutations; dependent on output text |
| *(TBD - Literature survey)* | | | | | |

---

## 3. Attack Surface of Tool-Using Agents

### 3.1 Direct Prompt Injection & Jailbreaking
- *Key questions to survey:* How effectively do existing defense prompts or system prompts prevent unauthorized tool calling when the user directly instructs the agent to ignore rules?
- *Citations to add:* (To be added based on empirical papers).

### 3.2 Indirect Prompt Injection
- *Key questions to survey:* What vulnerabilities emerge when an agent ingests untrusted third-party data containing instructions (e.g., documents, emails, synthetic database records)?
- *Citations to add:* (To be added based on empirical papers).

### 3.3 Confused Deputy & Parameter Tampering
- *Key questions to survey:* Under what conditions does an agent invoke valid tools with unauthorized arguments (e.g., cross-tenant record IDs)?

---

## 4. Policy Verification & State-Aware Evaluation

### 4.1 Runtime Verification in Software Systems
- *Survey area:* Classical techniques for monitoring execution traces against temporal logic or security automata.

### 4.2 Application to AI Agents
- *Survey area:* Emerging work that applies formal state-machine tracking or database diffing to evaluate agent actions.

---

## 5. Identified Research Questions & Hypotheses

1. **Research Question 1 (RQ1):** To what extent do prompt-level black-box evaluators fail to detect unauthorized tool actions when the agent fails to report the action in its natural language output?
2. **Research Question 2 (RQ2):** Does verifying execution traces and application state transitions against explicit formal policies (e.g., multi-tenant isolation) significantly reduce false negatives compared to output-based evaluators?
3. **Research Question 3 (RQ3):** What is the runtime and implementation overhead of state-and-trace verification relative to prompt-only evaluation?

---

## 6. References & Bibliography

*(Academic papers, standard specifications, and technical reports will be documented here as reviewed.)*

