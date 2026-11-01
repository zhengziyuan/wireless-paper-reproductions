# Synthetic ISAC iota helper cross-check (review candidate)

This is **not a reproduction of the paper or an AO validation**. It is a fixed-state test of the standalone MATLAB and Python `isac_iota_update` helpers using eleven fabricated input cases. The second guarded attempt exited normally: four cases with numeric outputs agreed within the comparator tolerance (`5e-14` relative and `1e-300` absolute), and seven invalid or degenerate cases produced the same expected error classifications. This is limited evidence about these inputs and binary64 arithmetic; it does not establish general equality or paper-reference agreement. The precise outputs and case-indexed comparisons are in the adjacent JSON files; the input cases are in `tools/isac-iota-dual-validation-v1/isac_iota_toy_crosscheck.m` and `compare_fixed_states.py`.

The first attempt **failed**: The monitor reported an unexpected top-level path and stopped the task; no usable result was recorded. Subsequent inspection found `MathWorks/MATLAB/R2025b/ddux` under the task directory, outside the original guard's allowlist; the log did not identify the exact triggering item. The retained second attempt counted that exact temporary subtree and preserved the original resource limits. The guard polls storage and is not a hard filesystem quota. Original local attempt records remain separate from this sanitized review copy.

## Rechecking the saved synthetic output

From the repository root, this uses only Python's standard library and checks the saved MATLAB output against the included Python helper:

```text
python -B tools/isac-iota-dual-validation-v1/compare_fixed_states.py strict/rotatable-isac/evidence/iota-synthetic-fixed-v2/matlab-fixed-states.json
```

The source files used for the guarded run are included at `strict/rotatable-isac/isac_iota_update.m`, `strict/rotatable-isac/isac_iota_update_v1.py`, `tools/isac-iota-dual-validation-v1/isac_iota_toy_crosscheck.m`, and `tools/isac-iota-dual-validation-v1/compare_fixed_states.py`. Their executed-content identities are recorded in `run-summary.json`; these are source identities, not authentication of the historical paper or its inputs.

To produce a fresh **synthetic-only** MATLAB fixture, start MATLAB with the repository root as its current folder. Set the environment variable `ISAC_SYNTHETIC_OUTPUT_DIR` to an existing writable data directory outside the repository, then run:

```matlab
outputFolder = getenv('ISAC_SYNTHETIC_OUTPUT_DIR');
assert(~isempty(outputFolder) && isfolder(outputFolder));
outputFile = fullfile(outputFolder, 'isac-iota-synthetic-new.json');
assert(~isfile(outputFile));
addpath(fullfile(pwd, 'tools', 'isac-iota-dual-validation-v1'), '-begin');
helperFile = fullfile(pwd, 'strict', 'rotatable-isac', 'isac_iota_update.m');
isac_iota_toy_crosscheck(outputFile, helperFile);
```

Then pass that new output file as the sole argument to the same Python comparator. The fixture refuses to overwrite an existing output. This is an optional local repeat of the eleven synthetic cases; it does not reproduce any paper scenario or apply the guarded run's storage monitoring.

## Parameter and mathematical boundaries

The author's positive safeguard epsilon has **not** been determined. The values 0.25 and 0.5 used here are synthetic test fixtures, never author parameters. Exact mode and a safeguarded denominator are distinct policies: a positive epsilon changes the denominator, potentially changing the solution and the objective. They must not be silently substituted for the original paper's algorithm. In exact mode, positive pattern energy with zero overlap has no finite minimizer under the represented positive-scale domain. When the pattern energy is zero and desired energy is positive, NMSE is one for any positive scale; the helper conservatively refuses to invent a scale rather than asserting that finite minimizers do not exist.

The test calls the two standalone helpers directly. It does not execute either prepared AO candidate, simulate a published scenario, assess physical feasibility, establish convergence, compare figures/tables, authenticate historical paper inputs, or verify the unknown epsilon.

## Prepared AO candidates still differ

The Python `isac_iota_policy_ao_v1.py` candidate only applies its relative-improvement stopping test when the improvement is nonnegative. It records any observed decrease in the W, RIS, rotation, scale or outer comparison and prevents `full_converged` when any such decrease occurred. The MATLAB source rendered by `prepare_matlab_iota_policy_v2.py` preserves its existing outer stopping expression and suppresses `full_converged` if any recorded *outer* objective increment is negative. These are different stopping/reporting semantics; this helper cross-check does not establish equivalence of the candidate AO trajectories. The current Python production `core.optimize` additionally rejects an outer decrease beyond `verification_tolerance` and can stop on a smaller negative increment, so the prepared Python candidate is not a claim of identical production stopping behavior. These descriptions refer to local prepared candidates; their AO integration sources are not part of this minimal helper evidence package. Both integrations still require independent scientific validation.

Only sanitized synthetic inputs, results, source identifiers and guard outcomes are presented here. No host username, process ID, machine identifier, absolute filesystem path or local log is included. This review copy is not a release or scientific acceptance.
