# Validation evidence and limits

This directory contains actual outputs from the reduced shared-fixture Python and MATLAB executions, the full-output parity report, and a manifest of runtime versions and source/fixture hashes.

- `python/` and `matlab/`: numerical outputs and package-specific checks from each runtime.
- `parity.json`: pass/fail records, tolerances and output hashes. False package checks fail validation even when both languages agree.
- `manifest.json`: hashes tie the results to exact package sources and fixtures, not merely a paper title.
- `iteration-traces.png`: plots of newly computed fixture optimization histories, not original paper curves.

The package checks cover selected analytic gradients, physical identities, feasibility, and solver diagnostics. Cross-language agreement alone does not establish scientific correctness, exhaustive robustness, global optimality, or correspondence to every published figure. Independent invariance/regression tests are in `tests/test_models.py`. Public-source verification is limited as described in each `source_map.json`; the hotspot module's final journal full-text verification is still pending.

To refresh evidence after changing code or inputs: run both languages, run `validate_python.py` and `validate_parity.py`, then `export_validation.py --matlab-version <actual-runtime-version>`. Never relabel old outputs as current validation of modified sources.
