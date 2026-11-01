# ADR-002: Local Research Token Authentication and Append-Only In-Database Audit Logging

**Status:** Accepted  
**Date:** 2026-10-30  
**Deciders:** Senior Software Architect, Harness Engineer  
**Milestone:** 002 — Secure Synthetic Target Application  

---

## 1. Context & Problem Statement

To evaluate the security of tool-using AI agents against multi-tenant isolation policies (such as SEC-01), the target application requires:
1. A deterministic, offline method to establish an authenticated principal per request without depending on external identity providers (OAuth2, Auth0, Keycloak) or heavyweight cryptographic token services.
2. An append-only audit trail capturing authorization decisions and operational outcomes as internal ground truth evidence.
3. Strict decoupling between authorization evaluation (`ALLOW` vs. `DENY`) and operational outcomes (`SUCCESS`, `NOT_FOUND`, `ERROR`).
4. Strict protection against leaking sensitive data (canary tokens, credentials, or internal audit traces) in client-facing error responses.

---

## 2. Decision

We decide to implement:
1. **Deterministic Local Bearer Authentication:**
   - Clients supply standard `Authorization: Bearer <token>` headers.
   - Pre-shared research tokens map directly to synthetic tenant principals (`test-token-user-a` $\to$ `user_a`, etc.).
   - Untrusted request bodies, query parameters, or client-supplied headers (`X-User-Id`) are never used to infer or establish identity.
   - Missing or invalid tokens result in HTTP 401 Unauthorized with `WWW-Authenticate: Bearer`.
2. **Append-Only SQLite Audit Logging:**
   - An `audit_events` table records all protected access and modification attempts.
   - The application layer exposes no `UPDATE` or `DELETE` methods for audit records.
   - Authorization decisions are categorized as `ALLOW` or `DENY`, completely distinct from execution outcomes (`SUCCESS`, `DENIED_UNAUTHENTICATED`, `DENIED_UNAUTHORIZED`, `NOT_FOUND`, `ERROR`).
3. **Decoupled Error Responses:**
   - API error responses (401, 403, 404, 422, 500) return sanitized `{"detail": "..."}` messages. Internal audit IDs, SQL errors, and sensitive record contents are never reflected.

---

## 3. Consequences & Trade-offs

### Positive Consequences
- **Repeatability & Zero Network Latency:** Tests run deterministically and quickly (< 2 seconds for complete suite) without external network dependencies.
- **Explicit Ground Truth:** Every request produces a structured, queryable audit record for later comparison with the independent evaluator's trace recordings.
- **Clean Defense in Depth:** Backend authorization is enforced on primary keys and foreign keys in SQLite, preventing agents or callers from corrupting tenant boundaries regardless of prompt persuasion.

### Limitations & Known Trade-offs
- **Not Production Authentication:** Tokens are plain strings stored in configuration; this design is strictly for offline research evaluation.
- **SQLite Audit Integrity Limitation:** Because SQLite is an embedded file on disk without hardware-enforced write-once guarantees, an adversary with local OS filesystem access or raw SQL injection could tamper with audit records out-of-band. External corroboration by `security_engine` remains essential.

