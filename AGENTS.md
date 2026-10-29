# Coding Agent Instructions & Harness Guidelines

This document provides concise, enforceable instructions for AI coding assistants working in this repository. All contributing agents must follow these engineering principles.

---

## 1. Core Operating Principles

1. **Inspect Before Editing**: Always examine existing files, directories, and configuration before proposing or executing modifications. Never assume the presence or contents of a file.
2. **Small, Atomic Changes**: Make focused, incremental changes. Each change must have a single clear purpose that can be reviewed and tested independently.
3. **Explain Architectural Decisions**: Document why a change is made, what trade-offs were considered, and how it aligns with established architecture and threat models.
4. **Run Real Checks & Verify**:
   - Execute relevant automated tests, linters, or schema validations after modifying code.
   - **Never invent or assume test results.** Report only actual command outputs.
   - If a test or command cannot be executed, explicitly state that it was not run.
5. **Epistemic Invariant**:
   > **Absence of a test failure does not prove the presence of security.**
   Never claim a security property is "satisfied" or "secure" merely because an adversarial test did not produce a violation. Frame findings strictly as: *"No violation observed under tested conditions."*
6. **Evaluator Independence**:
   The agent under test must **never** be granted authority to determine or influence its own security verdict. Evaluation logic, trace collection, and policy verification must remain outside the target agent's execution and trust boundaries.
7. **Document After Milestones**:
   Update `README.md`, status tables, and relevant documentation files upon completing a milestone or significant structural change. Clearly distinguish between **Planned**, **Implemented**, **Tested**, and **Unverified** capabilities.
8. **Safety & Secrets**:
   - Never commit API keys, secrets, or real personal data.
   - Maintain `.env.example` with non-sensitive placeholders only.
   - Use synthetic, deterministic test data exclusively.

---

## 2. Feedback Loops & Verification Checklist

Before reporting completion of any task, run through this checklist:
- [ ] Did you inspect existing files before making edits?
- [ ] Are changes scoped strictly to the current milestone or task?
- [ ] Were all automated checks executed, and their real outcomes captured?
- [ ] Is all newly introduced terminology grounded without unverified novelty claims?
- [ ] Were documentation files updated to reflect current implementation reality?

