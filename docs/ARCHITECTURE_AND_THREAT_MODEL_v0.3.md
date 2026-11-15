# Architecture and threat model v0.3

**Scope:** a Linux two-user demonstration of a server-owned execution boundary for *mock* file, drafting and messaging actions. The larger constitutional/AI-governance framework is deliberately outside the scope of the measured prototype.

## Objective and boundary

A good gate should facilitate verified legitimate activity, challenge anomalies proportionately, and prevent actions exceeding authority. It should not indiscriminately deny activity. This is the **legitimate-access-facilitation** criterion (AG-04), alongside caller trust establishment (AG-01), proposed contextual intelligence (AG-02) and human-governed adaptation (AG-03).

```
  HUMAN TASK / AUTHORITY           UNTRUSTED EXTERNAL DOCUMENT
             |                                |
             v                                v
       [ Limited agent process (UID 29172) ]
             |  signed, structured requests
             v
         LOCAL UNIX SOCKET
             |
             v
    [ Gateway + mock executor (UID 29171) ]
       | kernel UID check + HMAC + nonce
       | action schema, caller capability
       | server-owned document classifications
       | allowlist, human approval or contextual WAIT
       | one-use execution + private audit
             |
             v
      [ Mock files / outgoing messages ]

        Human operator (UID 0 in demo) --(approve/revoke)--> Gateway
```

The agent process has **no filesystem permission** to read service-only configuration or audit records. It can still submit a signed request with its own valid credential; identity is not equivalent to authority. We tested denial when the agent attempts to read service state directly and when it submits an operator request. We have **not** confined the agent's general network/filesystem access, executed arbitrary agent-generated code, or proven complete mediation over arbitrary tools.

## Explicit authority model

- **Source of authority:** server-owned caller registry, action schema, document classifications, human operator decisions and allowed recipients.
- **Untrusted:** contents of externally retrieved documents, agent-provided rationales (not used as approvals), caller claims of sensitivity and free-text instructions.
- **Trusted to limited extent:** Linux peer UID and registered HMAC key possession. Either can be insufficient against a compromised authorised caller. Production must address key protection, identity lifecycle and operator authentication.
- **Human authority:** an authorised operator can approve a specific pending request, revoke it, or change classification. Approval is scoped to the exact pending action; the agent cannot propose and grant its own approval.
- **Safe execution:** a single-threaded server serialises check and mock effect. This does not generalise to multi-threaded or external irreversible operations.

## Threat catalogue and tests

| Threat | Mechanism | Test evidence | Remaining risk |
|---|---|---|---|
| Forged caller ID | Server checks kernel UID, registered ID and signed body | `test_caller_forgery_rejected` | Valid credential theft, compromised trusted process |
| Tampered request | HMAC over canonical request | `test_hmac_tampering_rejected` | Agent can sign its own malicious request |
| Replay | Nonce registry | `test_hmac_replay_rejected` | Nonces lost on process restart |
| Caller-supplied risk | Strict schema and server-side resource labels | `test_schema_rejects_caller_risk_claim` | Incorrect metadata/classification |
| Secret document to external recipient | Binding to resource label/recipient policy | `test_restricted_exfiltration_blocked` | Alternative channels outside gateway not isolated |
| External prompt-injection text | Policy gate rejects unauthorised content-driven tool call | `test_actual_unsafe_document_drives_agent_decision` | Agent is a parser, not an LLM |
| Content-driven allowed action lacking actual user permission | Context reviewer observes recent suspicious external read | `test_context_reviewer_observes_untrusted_read` | Detection is brittle; noncausal; evasion and false positives |
| Overblocking legitimate request | Quoted training example triggers `WAIT` | `test_reviewer_has_false_positive` | No automated verification-resolution flow yet |
| Private file bypass | Separate Unix UID & mode `0700` | `test_private_state_denied_by_kernel` | Root/host compromise, side channels, other APIs |
| Operator impersonation | Operator channel restricted by peer UID | `test_agent_cannot_impersonate_operator` | Root UID is not a proper human authentication design |
| Approval replay | Pending exact action + consumed approval | `test_approve_then_commit_single_use` | Crash recovery/in-flight external tool semantics |
| Approval revocation | Server-owned approval state | `test_approve_revoke_then_no_commit` | Changes after external tool commit irreversible |
| Approval expiry | Server monotonic clock | `test_approval_expiry_uses_server_time` | Server restarts do not preserve grants |
| Changed conditions | Commit-time hard policy re-evaluation | `test_reclassification_rechecked_at_commit` | Some policy context/metadata remains unmodelled |
| Audit tampering by agent | Service-only filesystem and hash verification | `test_audit_write_denied_to_agent` | Root/operator can modify log and recompute chain |

## Why the AI reviewer remains a proposal

The current contextual review is deliberately **deterministic**: if a caller recently read an external document containing a literal suspicious command pattern, it places otherwise permitted consequential requests on `WAIT`. It demonstrates the *location of an intelligent reviewer in the architecture*, not the capabilities of an intelligent reviewer. It is vulnerable to both false positives and slight prompt variations and has no reasoning, investigation or self-improvement.

A genuine small AI reviewer would need a narrowly specified task, independent evidence access, an explicit threat model and authority limited to advice/escalation. We should test whether it reduces unsafe executions **without disproportionately increasing false blocks or human interruptions**. It must never change binding authorisation policies based solely on its own output.

## Human-governed adaptive oversight: proposed future work

Humans may convert repeatedly confirmed patterns into **specific, reviewed rules**, or use labelled examples to improve the reviewer. Each change should have its own provenance, validity range, regression tests, deployment approval, rollback and audit. One human approval of a single action must not silently become broad permanent authority. This learning mechanism is **not implemented** in the v0.3 service.

## Failure and release boundaries

- A host administrator or root user can bypass the mode-based boundary.
- A generic LLM/code agent may have OS APIs outside the mock tool path; this test offers no broad guarantee of preventing exfiltration.
- The HMAC key lives with the authorised caller and thus authenticates a *principal*, not the correctness of its judgement.
- No rate limits, denial-of-service controls, adversarial prompt distributions, model access, production secrets, external tool atomicity, durable restart recovery, security proofs or independent tests are present.
- This is a mock-only environment. No real emails are sent; no external data is deleted or transmitted.
