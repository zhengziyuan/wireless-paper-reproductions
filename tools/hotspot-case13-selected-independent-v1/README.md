# Independent exact recheck of three saved case-13 states

This standard-library reader independently recomputes the saved-state
assessment from the retained selected-state projection and NHU moment input.
It does not read the original trajectory, run an optimizer or compute new
channel moments. Its calculations treat the saved binary64 values as exact
rationals. The inputs and earlier assessment remain subject to the same
unverified historical producer and non-atomic-event limitations.

For NoRIS, TwoStage and AO, it compares all 45 NHU moment-based margins and
all 45 saved-Psi Hermitian-part margins to the retained report. The full-J
interference set includes every stream other than the desired NHU stream. It
also verifies the 45 exact anti-Hermitian residual pairs, power and phase
errors, selected/final numerical identities, NoRIS phase applicability, and
positive versus nonnegative QoS flags. It reconstructs the matrix quadratic
form directly using conjugate-transpose multiplication. A zero QoS margin is
nonnegative but not strictly positive.

The retained same-machine run in `recorded-recheck.json` matched all these
reported quantities exactly. This is a second calculation on common saved
inputs, not an independent original experiment. In particular, matching the
binary64 computation does not authenticate the historical source, prove
mathematical convergence, establish full physical feasibility under the
publisher's model, validate MATLAB/Python parity, or verify original figures.
Any exact phase-equality failure is preserved; it is not silently converted
into a tolerance-based result. In the implemented NoRIS branch, phase is
irrelevant to these constraints and its exact modulus is marked inapplicable.

The input files are the adjacent published
`validation/hotspot-case13-selected-physical-v1/selected-input.jsonl.gz` and
`recorded-assessment.jsonl`, together with the already published
`tools/hotspot-case13-evidence-v1/moment_projection.json`. Decompression is
bounded and occurs in memory; no extra source or image copy is created.

From the repository root, using Python's standard library:

```text
python -I -S -B tools/hotspot-case13-selected-independent-v1/verify_selected_exact.py
python -I -S -B tools/hotspot-case13-selected-independent-v1/test_verify_selected_exact.py
```

The synthetic tests include a complex conjugation counterexample, all 45
synthetic constraints, zero margin, altered report, wrong case, a NoRIS phase
change and incomplete terminal. They do not constitute paper-level tests.
