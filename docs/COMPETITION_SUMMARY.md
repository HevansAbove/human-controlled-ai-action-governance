# Human-Controlled AI Action Governance

**A layered, proportionate and verifiable control boundary for consequential AI-agent actions**

## The problem

An agent can be instructed to behave responsibly yet still propose actions based on ambiguous requests, forged content or outdated approvals. A refusal after a consequential operation cannot undo the action. The proposed safeguard places authority checks and execution in a separate service, while treating the agent as a requester rather than the source of its own permission.

## Demonstrated mechanism

A limited agent and mock executor operate under separate Unix identities. The protected executor validates caller identity and signed requests; independently checks mock document classifications, capability scope and permitted destinations; enforces exact, single-use and revocable operator approvals; and records mock actions in a basic audit chain. Decisions include ACT, ASK, WAIT and BLOCK. A deterministic pattern reviewer adds caution after suspicious document content; it is **not a miniature AI**.

The design aims to **allow routine authorised activity, verify ambiguity, defer decisions requiring human review and block prohibited action**, rather than reflexively rejecting requests.

## Empirical results

Curated, paired **14 scenario** comparison (eight designated legitimate; six designated unauthorised):

| Configuration | Unauthorised mock actions executed / 6 | Legitimate mock actions executed immediately / 8 | Legitimate deferred / 8 |
|---|---:|---:|---:|
| Baseline (no policy gate) | 6 | 8 | 0 |
| Rules-only gate | 1 | 5 | 3 |
| Rules + deterministic contextual reviewer | 0 | 4 | 4 |

These are *hand-designed* scenarios, not an independent security benchmark; the reviewer adds a false positive, and deferred legitimate actions are not counted as completed. The archived automated code suite contains 22 test cases (18 cross-process plus four offline adapter tests). The earlier completed run reported all 22 passing; see test rerun note in README. Only a limited subset of agent behaviours and local pathways are covered.

## Separate manual live-model observations

The operator also conducted three **Google AI Studio** manual function-calling trials with fictional tools. A model requested legitimate document sends, rejected embedded malicious instructions in the observed cases, and sought human confirmation after the operator manually supplied an ASK response. These are reported observations, **not** results from the integrated Python enforcement system. The original external transcript is not included; see `docs/GEMINI_MANUAL_TRIALS.md`.

## Threat model and contribution

The contribution is a **small reproducible integration and evaluation** of existing security principles—independent enforcement, least authority, constrained execution, approval binding and audit—plus a human-centred design for intelligent contextual verification and adaptive oversight. It does **not** claim those underlying mechanisms are novel. The proposed miniature-AI reviewer and human-governed model improvement remain future work.

## Limits

The service protects **synthetic operations only**; it does not fully sandbox arbitrary LLM code, prevent network exfiltration, authenticate real human identities, deliver real messages, or prove protection from unrestricted autonomous agents. A deterministic agent was used for comparative benchmarks. Docker steps were not independently verified, and hosted API integration was tested only with offline fixtures. See the detailed architecture and technical report for assumptions and deficiencies.

## Reproducing

See `README.md` for Linux test setup, commands, exact recorded results and limitations. All comparison result CSV files are included. No real credentials, personal datasets or production integrations are necessary.
