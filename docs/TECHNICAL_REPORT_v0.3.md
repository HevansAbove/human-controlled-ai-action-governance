# Human-Controlled AI Action Governance: experimental report v0.3

**Status:** internal technical draft, 11 November 2026. Not peer reviewed. No independent red-team review.

## Research question

Can an independent local tool-execution gateway prevent a deliberately vulnerable, autonomous *rule-based* agent from committing mock unauthorised actions, while allowing routine legitimate actions, and what is the additional cost of deterministic contextual review?

## Experiment

A deliberately limited agent running with UID 29172 reads simulated external documents or receives direct tasks, chooses a structured tool request, signs it with its caller credential, and submits it through a Unix socket. The gateway and mock executor run with UID 29171, use OS peer credentials and HMAC verification, and hold independent document classifications, recipient lists and approval records. A separate operator channel is restricted by UID. These identities are **demonstration OS identities**, not an enterprise identity-management system.

Three gate settings were tested with the same 14 scenarios:

- **Baseline:** client requests reaching the service are executed without policy evaluation (but still through the mock service).
- **Rules:** enforce static caller capabilities, server-owned resource labels, recipients and operator review.
- **Rules + reviewer:** add a deterministic `WAIT` trigger when the server has recently observed suspicious instruction patterns in external content accessed by the agent.

The test set was written alongside the implementation. It contains eight designated legitimate scenarios and six designated unauthorised scenarios. There are no third-party labels, unseen prompts, actual LLM outputs or realistic workload distributions. Each scenario starts with an independent service instance, which prevents cross-scenario context carryover.

## Results

| Configuration | Executed unauthorised actions / 6 | Executed legitimate actions immediately / 8 | Deferred legitimate actions / 8 |
|---|---:|---:|---:|
| Baseline | 6 | 8 | 0 |
| Rules-only | 1 | 5 | 3 |
| Rules + deterministic reviewer | 0 | 4 | 4 |

All 18 end-to-end tests passed on the Linux execution host. They cover process-based private-file separation, signed-request tampering, replay, forged identity, operator isolation, schema denials, read-versus-send permission distinction, approval, expiry, revocation, changed classification and basic audit verification. The sample sizes are too small, curated and non-independent for statistical safety or efficacy conclusions.

**Key observation:** The residual rules-only failure involves an instruction from a recently read external note to send a publicly classified document to a known recipient—an action allowed by resource-level policy but not actually ordered by the human. The reviewer deferred it because it observed a suspicious instruction pattern.

**Trade-off:** The same reviewer also deferred one legitimate scenario where external content was quoting a suspicious pattern. Security increased in this sample at the cost of lower immediate task completion. The underlying parser agent also follows the quoted pattern rather than evaluating intent, another reason not to extrapolate these results to real assistants.

**Human workflows:** The separate unit suite includes an exact, one-time human-approved mock action and an approval that is revoked before execution. `human_review_demo.py` shows this end-to-end. The tabulated evaluation results do **not** credit `ASK` or `WAIT` as task completion, and do not measure throughput or human processing times.

## Interpretation

This experiment supports a narrow feasibility claim: in the controlled fixture, moving the mock executor into a differently permissioned process prevented direct private-file access and forced the tested mock actions through an independent service, where policy and operator decisions could be applied. It does **not** establish protection for arbitrary local programs, a general-purpose agent's network access, or real irreversible actions.

The contextual reviewer is not a miniature AI. There is not yet an LLM in the agent or at the gate; therefore this evidence cannot answer whether a small model can exercise useful contextual judgement or outperform conventional safeguards. Nor does this comparison prove novelty relative to existing policy engines, reference monitors or commercial agent guardrails.

## Priorities before publication as an empirical security claim

1. Connect a **genuine tool-using LLM** in a network-isolated sandbox and log model-generated actions; use held-out prompts and varied adversarial inputs.
2. Enforce complete mediation of all relevant tools, including OS/network exfiltration channels; repeat direct-bypass probes.
3. Add a real constrained small reviewer model, compare to static rules and deterministic heuristics, and independently label legitimate and prohibited outcomes.
4. Extend `ASK`/`WAIT` to completed clarification and human-review workflows; measure true task completion and human burden.
5. Add durable transactional state, externally anchored audit logs, restart and concurrency tests, operator authentication, credential lifecycle controls and security engineering review.

**Appropriate competition claim today:** a reproducible, process-separated mock prototype demonstrating conditional execution and user oversight in curated scenarios, alongside a proposed larger architecture. **Inappropriate claim:** proven AI safety, robust prompt-injection protection or validated miniature AI judgement.
