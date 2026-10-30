# Threat Model

**Milestone:** 002 — Secure Synthetic Target Application  
**Status:** Backend Mitigations Implemented & Tested (*Agent and verifier layers planned*)

---

## 1. System Assets

In the context of the synthetic target application, the primary assets requiring protection are:

| Asset ID | Asset Name | Description | Sensitivity |
| :--- | :--- | :--- | :--- |
| **AST-01** | **Tenant Private Records** | Synthetic user documents, financial records, or notes belonging exclusively to a specific tenant (e.g., User B). | High (Confidentiality & Integrity) |
| **AST-02** | **Tool Execution Interface** | Capabilities exposed to the agent to query or mutate application state (e.g., `read_record`, `update_record`, `delete_record`). | High (Integrity & Authorization) |
| **AST-03** | **Application Database** | Persistent relational storage (SQLite) holding all tenant data. | High (Integrity) |
| **AST-04** | **Evaluation Audit Logs** | Execution traces and state diffs captured by the Security Engine. | High (Tamper-evidence) |

---

## 2. Trust Boundaries & Actors

### Actors
1. **Authenticated User A (Adversary / External Actor):** Possesses legitimate credentials for Tenant A. Interacts via natural language prompts with the AI agent. Assumed to be potentially malicious or acting as an adversarial tester attempting to breach multi-tenant isolation.
2. **Victim User B (Benign Tenant):** Legitimate tenant with confidential records stored in the database. Does not interact with User A's session.
3. **Target AI Agent (Untrusted Orchestrator):** Language model (Qwen 4B / Ollama) executing user instructions via LangGraph. Assumed vulnerable to prompt injection, jailbreaks, and logical confusion.
4. **Application Backend & Tools (Semi-Trusted Layer):** Implements business logic and data access. Vulnerable if tools rely naively on the agent's arguments without enforcing backend session authentication.
5. **Security Engine (Trusted Verifier):** Out-of-band evaluation harness that records and verifies state transitions and tool traces.

### Trust Boundaries
- **Boundary 1 (User to Agent):** Untrusted input crossing into the conversational interface.
- **Boundary 2 (Agent to Tools):** Agent-generated parameters passed to tool functions. The agent's reasoning must not be trusted as an authorization mechanism.
- **Boundary 3 (Target App to Security Engine):** One-way observation interface. The Security Engine observes the Target App, but the Target App cannot influence or read the Security Engine's state or verdicts.

---

## 3. Attacker Capabilities & Assumptions

The threat model assumes an attacker with the following capabilities:
- **Direct Prompt Injection:** The attacker can supply arbitrary text, jailbreak prefixes, roleplay instructions, and system prompt override attempts.
- **Indirect Prompt Injection:** The attacker can cause the agent to process data containing concealed adversarial instructions (e.g., in a retrieved shared document or simulated web/email payload).
- **Parameter Manipulation:** The attacker attempts to coax the agent into passing unauthorized parameters (e.g., passing User B's `record_id` into a tool call executed during User A's session).
- **No Direct DB Access:** The attacker does *not* possess direct SQL access or network access to the database; all interactions occur through the AI agent interface.

---

## 4. Identified Threat Vectors & Concrete Risks

| Threat ID | Threat Description | Attacker Objective | Concrete Risk |
| :--- | :--- | :--- | :--- |
| **THR-01** | **Unauthorized Cross-Tenant Read** | Access User B's private record via User A's prompt. | Confidentiality breach: Agent calls `read_record(record_id=B)` and prints contents to User A. |
| **THR-02** | **Unauthorized Cross-Tenant Modification** | Modify or overwrite User B's record via User A's prompt. | Integrity breach: Agent calls `update_record(record_id=B, ...)` corrupting User B's state. |
| **THR-03** | **Confused Deputy Tool Calling** | Trick agent into executing destructive tools (e.g., `delete_record`) without legitimate authorization. | Availability & Integrity breach: Unauthorized deletion of records. |
| **THR-04** | **Evaluation Evasion (Sycophancy / Masking)** | The agent performs an unauthorized tool call but crafts a benign natural language response to mislead black-box evaluators. | Evaluator blind spot: Prompt-level evaluators score as PASS while state was corrupted. |

---

## 5. Mitigations & Defense Layers

1. **Backend Ownership Invariant Checks (Target App Layer - Implemented in M002):** The API service layer strictly verifies that the authenticated caller (`principal_id`) matches `record.owner_id` for every protected read and modification. Unauthorized reads receive 403 with no record disclosure; unauthorized modifications leave persistent SQLite state unchanged.
2. **Deterministic Parameter Schemas (Target App Layer - Implemented in M002):** Pydantic schemas forbid tampering with ownership (`owner_id`) and reject arbitrary extra fields or empty modification bodies.
3. **Append-Only Internal Audit Log (Target App Layer - Implemented in M002):** Audit events capture principals, actions, resources, authorization decisions (`ALLOW`/`DENY`), and outcomes (`SUCCESS`, `DENIED_UNAUTHENTICATED`, `DENIED_UNAUTHORIZED`, `NOT_FOUND`, `ERROR`).
4. **Policy-Based Verification (Security Engine Layer - Planned M004):** Independent audit of the full trace and state delta. Even if the backend fails or the agent masks its response, the verifier detects the unauthorized read/write.

---

## 6. Out-of-Scope Threats

The following threats are explicitly out of scope for this research project:
- **Host OS & Infrastructure Compromise:** Attacks targeting the host operating system, Python interpreter binaries, or SQLite engine vulnerabilities.
- **Direct Database File Manipulation:** Attacks bypassing the application and writing directly to the `.sqlite` file on disk (SQLite audit-integrity limitation).
- **Network Denial-of-Service (DoS):** Exhausting local machine compute or Ollama VRAM through high-concurrency requests.
- **Physical Access:** Attackers with physical access to the test machine or local filesystem.
- **Cryptographic Breaks:** Attacks attempting to break standard cryptographic hashes or SQLite file encryption.

---

## 7. Status & Verification

Backend mitigation layers (1, 2, and 3) are **Implemented and Tested** at the direct API level. Agent-mediated threat resistance remains **Unverified** pending Milestone 003 bring-up.

