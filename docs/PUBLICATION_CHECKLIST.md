# Release checklist — before making the GitHub repository public

- [ ] Review the code and technical report; confirm public disclosure is acceptable. Repository has no open-source licence; do not add one without making an explicit licensing decision.
- [ ] Do not upload API keys, `.env` files, browser cookies, real personal details or internal private framework notes.
- [ ] Keep the original Google AI Studio transcript privately archived; optionally export a redacted copy as supplementary evidence. It is **not** included here.
- [ ] Confirm the uploaded repository root contains `README.md`, `service.py`, `harness.py`, `tests/`, `docs/`, `results_summary.json`.
- [ ] In GitHub, check `README.md` renders correctly and files are browsable without signing in.
- [ ] If using a test machine, run `python3 -m unittest discover -s tests -v` in a disposable Linux environment. The documented environment requires test-root privileges **inside an isolated VM/container**, not on a personal host.
- [ ] Do not imply the optional LLM adapter has completed live integrated tests.
- [ ] Submit the public repository URL using the official Drawerrr challenge form before 15 November 2026; retain submission confirmation.
