# Reproduction check — 14 November 2026

The archived test suite was rerun in the current Linux container (effective UID 0 inside this development environment), using:

```bash
python3 -m unittest discover -s tests -v
```

**Result:** `Ran 22 tests in 30.138s — OK` (exit code 0). These comprise 18 cross-process enforcement tests plus 4 offline model-adapter fixture tests. This rerun does **not** include a live model connected to the executor or an independently designed threat suite.

The repository includes historical CSV comparison outputs. The 14-scenario benchmark was not separately re-executed as part of this final check; refer to the saved outputs and `evaluate.py` for reproduction.
