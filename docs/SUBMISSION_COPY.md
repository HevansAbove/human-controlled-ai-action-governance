# Drawerrr submission — copy-ready description

**Title:** Human-Controlled AI Action Governance: A Layered, Verifiable and Proportionate Action Gate

**Affiliation:** Independent researcher

**One-paragraph description:**

We present a research prototype for governing consequential AI-agent actions through a separately permissioned execution gateway. Rather than relying on an agent's own safety instructions, a mock executor checks authenticated caller identity, action-specific permissions, data classifications, approved recipients and revocable, single-use human authorisation. The architecture distinguishes routine permitted activity from requests requiring verification or human oversight. In 14 curated simulated scenarios per configuration, an unguarded policy baseline executed six of six unauthorised mock actions; a rules-only gate executed one; and a rules-plus-deterministic-reviewer gate executed none, while deferring an additional legitimate request. All outcomes are limited to our constructed scenarios, and the contextual reviewer is **not a trained AI model**. Separate, manually orchestrated Gemini function-call trials illustrated model behaviour but were not connected to the Python gateway. We provide code, tests, threat model, limitations and reproduction instructions, and outline a future small-model reviewer with human-governed updates.

**Repository link:** [INSERT YOUR PUBLIC GITHUB REPOSITORY URL AFTER PUBLISHING]

**Suggested challenge category:** Safeguarding delegated actions; also relevant to information access and consequential decisions.

**Important:** Do not claim real-world security efficacy, autonomous LLM enforcement, 22/22 independently reproduced new tests, or a production-ready miniature AI. The original Gemini transcript has not been attached to this archive.
