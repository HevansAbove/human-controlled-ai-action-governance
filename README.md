# Human-Controlled AI Action Governance — competition prototype (November 2026)

**Start here:** [`Competition summary`](docs/COMPETITION_SUMMARY.md) · [`Technical report`](docs/TECHNICAL_REPORT_v0.3.md) · [`Threat model`](docs/ARCHITECTURE_AND_THREAT_MODEL_v0.3.md) · [`Manual Gemini trials`](docs/GEMINI_MANUAL_TRIALS.md) · [`Submission description`](docs/SUBMISSION_COPY.md)

**Evidence boundary:** The tested executor is a Linux-separated **mock** service and the benchmarking agent is deterministic, not a live LLM. The contextual reviewer is likewise deterministic, not a trained AI. An optional LLM adapter was tested with **offline fixtures**, while three separate human-operated Google AI Studio trials used **manually entered tool responses**. Do not merge the two evidence streams into a claim of live LLM enforcement.

**Release:** No open-source licence is granted in this archive. The author retains rights; review terms before public release. No secrets should be committed.

---

# Human-Controlled AI Action Governance — v0.3

**Research prototype. Not a production AI agent or security product.**

This work explores the proposition that a separate, enforceable governance boundary should **facilitate legitimate actions and stop or escalate unverified ones**. It develops the v0.2 in-process demonstration into a small **two-process, two-UID Linux simulation**: a constrained decision-making agent reads a mock external note, proposes a tool action, and a separately permissioned gateway decides whether a mock side effect occurs.

The aim is evidence for a narrow architectural claim, **not** a claim of preventing arbitrary LLM attacks.

## What is actually new in v0.3

- A separate executor service under its **own Unix user ID**, holding mock document state and execution logs in a service-only directory; the agent runs under another ID.
- Linux `SO_PEERCRED` checks of caller and operator process identities; HMAC-SHA256 integrity on agent requests. A valid caller credential alone never grants unrestricted approval.
- A **single mock tool interface** (read, send, save draft, delete) mediated by the gateway; no actual messages are sent and no real files are deleted.
- Independent resource labels and recipient allowlists, decision outcomes `ACT`, `ASK`, `WAIT`, `BLOCK`.
- Server-owned monotonic time for human approvals, explicit revocation, exact action binding and single-use execution.
- A demonstration of the gate observing a prompt-injection-like string in a retrieved document and preventing a later tool action; the **agent is a deterministic parser**, deliberately vulnerable to following such instructions.
- A deterministic contextual reviewer that sometimes catches an additional unauthorised action but **also produces a false positive**. **It is not an AI model.**
- Eighteen real cross-process tests and a curated, three-way, 14-scenario comparison.

## Run safely

**Option A: disposable Linux VM/container with root inside the VM/container.** The harness requires root *inside its test environment* to assign distinct unprivileged UIDs (`29171` service, `29172` agent). It stops immediately instead of silently running an insecure simulation if the required Linux features are absent. Never use production files or credentials.

```bash
python3 -m unittest discover -s tests -v
python3 evaluate.py
python3 human_review_demo.py
```

**Option B: an isolated Docker container (recommended for most reviewers):**

```bash
docker build -t action-governance-demo .
docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,exec,nosuid,size=64m \
  --cap-drop ALL --cap-add SETUID --cap-add SETGID \
  --cap-add CHOWN --cap-add DAC_OVERRIDE \
  action-governance-demo
```

The container recipe is provided as a convenience and **has not been exercised in the development environment**. Python tests were executed directly in a Linux root-operated sandbox. No third-party Python packages are required. The shell and process permissions in these examples are strictly for the mock environment.

`evaluate.py` writes `results.csv` and `results_summary.json`; the versioned archive also contains outputs from the completed runs. Use `python3 evaluate.py reviewer` to run one configuration (also accepts `baseline` or `rules`).

## Curated results (14 scenarios per configuration)

| Configuration | Unauthorised actions executed (of 6) | Legitimate actions executed immediately (of 8) | Legitimate actions deferred (of 8) |
|---|---:|---:|---:|
| Unguarded policy baseline | **6** | 8 | 0 |
| Deterministic rules-only | **1** | 5 | 3 |
| Rules + deterministic contextual reviewer | **0** | 4 | 4 |

Important: `ASK` and `WAIT` do **not** count as completed legitimate actions; no human follow-through is included in this comparison. Separate end-to-end tests and `human_review_demo.py` demonstrate approval, revocation, expiry and exact-authorisation execution. All scenarios were authored by us, not independently sampled or validated. These numbers must **not** be presented as a general safety rate, benchmark score or model performance evaluation.

The contextual reviewer blocks one prompt-injected request that the rules-only configuration permits, but additionally defers a *legitimate* request because its source document merely quotes a suspicious phrase. That trade-off is a real limitation of this prototype.

## Security boundary and its limits

This experiment shows **OS-enforced private-file separation for this service** and server-mediated *mock* actions under the tested Linux user separation. It does **not** provide a full sandbox for arbitrary AI-generated code, prevent arbitrary network activity, establish tool authority over all OS actions, or protect against root/host compromise. An agent that has read a secret might be able to leak it through other channels in a less constrained environment. The single mock send interface prevents arbitrary free-text payloads by design; this narrows the claim considerably.

There is no LLM, no small model, no real human account identity provider, no real messaging API, no secure enclaves, no production key management, no tamper-proof audit, no durable reconciliation after a crash, no concurrent execution or adversarial independent red team. A hash chain is not an externally anchored log and the operator is authenticated by kernel UID (root in the demo), which is not a deployable human-login method. This prototype should not be installed with system-wide privileges or exposed to real callers.

## Files

| Path | Purpose |
|---|---|
| `service.py` | Mock protected executor and policy gate |
| `agent.py` | Separate, deterministic tool-using agent (not an LLM) |
| `wire.py` | Local Unix-socket protocol and signed requests |
| `harness.py` | Ephemeral, OS-UID-separated test environment |
| `operator.py` | Prototype operator client |
| `human_review_demo.py` | Full human-approval and revocation example |
| `evaluate.py` | Curated three-configuration comparison |
| `tests/test_end_to_end.py` | Eighteen cross-process tests |
| `docs/ARCHITECTURE_AND_THREAT_MODEL_v0.3.md` | Threat model and architecture |
| `docs/TECHNICAL_REPORT_v0.3.md` | Evaluation and caveats |
| `results.csv`, `results_summary.json` | Actual local test outputs |

## Research questions for v0.4

1. How would an actual LLM agent behave under the **same user instructions and external observations**, rather than the intentionally vulnerable parser?
2. Does a real small-model reviewer outperform deterministic checks on **held-out, independently labelled** legitimate and hostile cases?
3. Can `WAIT` lead to verified clarification and proper human review without creating excessive friction?
4. How would a full OS/container sandbox prevent access to non-gateway tools and exfiltration channels?
5. Can independently evaluated, human-approved rule updates reduce repeated escalations without silently expanding authority?

## Public release and rights

The package is intended for **private repository review first**. No public-code licence is supplied here; choose any eventual release terms deliberately. Posting code publicly does not by itself prove the wider framework, originality, competitive standing or authorship of all underlying security ideas.

## Experimental model integration (v0.4 addition)

A separate **optional** model bridge is available in [`llm_adapter.py`](llm_adapter.py).
See [`LLM_INTEGRATION_GUIDE.md`](LLM_INTEGRATION_GUIDE.md) for configuration,
run steps, limitations, and required API credentials. The bridge's 4 new tests
use offline fixtures; **no live LLM calls have been run and no real-agent safety
numbers have been established**. The original v0.3 18 cross-process tests
continue to pass (22 tests total).
