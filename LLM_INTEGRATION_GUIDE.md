# Optional LLM integration (v0.4 adapter experiment)

**Status:** The `llm_adapter.py` tool bridge is implemented and tested against offline model fixtures. **No real OpenAI API requests or actual LLM behaviour have been tested in this environment.** Do not describe the offline test results as model-level findings.

## What it does

- Uses a hosted tool-calling model to generate proposed calls to four named *mock* tools.
- Validates the proposed tool names and argument shapes.
- Routes each proposal through the existing v0.3 agent process and UID-checked local governance gateway.
- Relays `ACT`, `ASK`, `WAIT`, or `BLOCK` outcomes to the model.
- Reports mock execution and audit records. No actual email is sent and no production files are changed.

The hosted model is called by a **trusted controller**, not by a jailed process. The controller has more privilege than the agent. This is a model-originated tool-call experiment, **not proof of an isolated network-enabled LLM agent**. In an authentic security-deployment test, the model broker must be isolated from both the executor's credentials and direct tool access; network egress must also be constrained.

## Prerequisites

1. An OpenAI API project, API key, and credits/billing. A normal ChatGPT Plus subscription does not supply API credits automatically.
2. A disposable **Linux** VM/container that supports two unprivileged Unix IDs, with Python 3.9+ and ability to make outgoing HTTPS requests to the model API. Current v0.3 `Sandbox` requires root **inside that disposable test environment**. Never run as root on a personal workstation or on a production machine.
3. `python -m pip install openai` *inside the test environment*.
4. Make the API key available only as the environment variable `OPENAI_API_KEY`. Never paste it into chat, include it in a command screenshot, or commit it to GitHub.

## Commands (inside an isolated Linux test VM)

```bash
python3 -m unittest discover -s tests -p 'test_llm_adapter.py' -v
python3 llm_adapter.py --mode reviewer --scenario legitimate --model gpt-5-mini --output legit_model.json
python3 llm_adapter.py --mode reviewer --scenario untrusted_note --model gpt-5-mini --output injected_model.json
```

To compare systems, rerun each scenario with `--mode baseline`, `--mode rules`, and `--mode reviewer`; use multiple scenarios and repeat runs. All documents, credentials and recipients created by `Sandbox` are synthetic. Never let the model call unrestricted shell or internet tools in this experiment.

### Known limitations

- Live API calls have **not** been executed in this development environment. SDK availability/model access and API/billing must be verified by the person running it.
- The same model can behave differently across runs. Disclose model name, date, prompts, parameters, repetitions and all failures.
- A hosted model sees synthetic document content returned by the mock gateway; do not replace it with confidential information.
- The historical v0.3 mock policies and curated scenarios are not a statistically valid security benchmark.
- The network-capable controller and an agent in a Linux UID boundary do not prove complete sandboxing. A production-strength evaluation requires a broker with no gate credentials and an agent environment with a strict network policy.
