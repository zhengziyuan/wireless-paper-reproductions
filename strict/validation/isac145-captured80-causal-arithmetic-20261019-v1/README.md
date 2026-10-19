# ISAC case145: actual80 rejected RCG trials and independent arithmetic diagnosis

This packet retains one actual failed RCG block in original case145
(power-b2,28dBm, realization45), from the first original `Rot-BS & Rot-RIS`
scheme: phase call27, RCG iteration474. It includes the full M4/N36/K2/A66
state, six streams, unchanged complex radii, previous PR operands and all80
actually tested trial vectors. The five original capture files are byte exact
(146,414 bytes), including the full scenario and frozen binary64 channel fields.
This is a diagnostic prefix, not a completed six-scheme result.

The original subtractive binary64 evaluator rejected **all80** actual trials.
Independent MP80 and MP100 evaluations accept precisely zero-based trials
**12–34:23 trials**, both with full physical paths and with exactly promoted
frozen binary64 channel fields. All four complete80-row reports are included.
Each preserves the actual trial alpha, objective, objective increment, original
slope Armijo requirement and original/stable floating errors. The original capture diagnostic naturally returned0 after saving the failed
block, with its12 watched source/job bytes closed. Both saved-data audit
processes naturally returned0 and their named source/input bytes closed.
These are actual diagnostic/audit completions, separate from convergence.

The stable self-excluded-interference evaluator first accepts trial12,
alpha=0.000244140625. That stored trial is accepted in all four MP lanes.
For the full-physics MP100 lane its increase is about1.052630507e-10,
above the unchanged original requirement about3.018744120e-14.
This isolates an implementation arithmetic rejection at this saved state;
it does not establish an error in the original paper's theory.

The stable floating evaluator also accepts trials35–79, which are **45 false
accepts** against each MP lane. The complete stable80-decision sequence is
therefore not certified. Those tail trials would not execute if the first
accepted trial12 were taken; they remain in this packet as explicit negative
evidence. A new stable trajectory also has changed derivative arithmetic and
cannot be inferred from this old stored PR direction.

All24 complex W,36 complex RIS and6 real rotation derivative components at
this fixed state pass the existing absolute1e-5 component bound at MP80/100.
W/RIS references are independent analytic derivatives; the rotation reference
uses MP central differences at1e-20. This component bound is not a solver stop.
The independently evaluated normalized RIS gradient is about1.85328e-4,
above the original1e-6 stop: **the gradient stop is not satisfied**.

The original RCG500 cap,80 backtracks, Armijo1e-4, factor0.5 and gradient1e-6
are preserved in `actual-failure.json` and `original-scenario.json`. Their
numerical-control provenance remains the disclosed implementation settings;
this package does not relabel unreported caps as author-reported budgets.
The original failure is retained. Complete trajectory repair, original-budget
whole-case convergence, MATLAB agreement and original figure/reference
agreement remain unaccepted. No full-paper PASS follows from these audits.

From the repository root, with repository requirements and `mpmath` installed,
use fresh output destinations to repeat the saved-operand checks:

```text
python tools/isac-line-search-replay/audit_failure.py --capture strict/validation/isac145-captured80-causal-arithmetic-20261019-v1 --output-dir new-isac145-all80-MP-audit
python tools/isac-line-search-replay/audit_stable_derivatives.py --capture strict/validation/isac145-captured80-causal-arithmetic-20261019-v1 --output new-isac145-all-gradient-audit.json
```

These commands read the saved operands and do not run an optimizer or draw a
channel. The four unchanged strict sources and auditor dependencies are bound
by `captured-source-binding.json` and `provenance.json`; different source
versions must not inherit this claim. The captured Python3.12.14/NumPy2.5.3
runtime fingerprint is preserved separately from a checking host's runtime.
The checking host need not fabricate a historical bitwise match across BLAS
or physical-path rounding. Full-physics and frozen-field references remain
separate, and every stored radius is used unchanged.

`manifest.json` binds every included file. `provenance.json` identifies exact
copies and the original receipt digests. The two small `evidence` projections
remove local absolute paths and next-trajectory command metadata while
retaining every actual causal row, count, gate and source digest. The11 saved
input/numeric report files were not edited. Preparation of this publication
packet performed no new MP evaluation, optimization, Monte Carlo or RNG call.

The separately published [three-fixed-state arithmetic candidate](../isac-stable-interference-dual-three-states-20261019-v1/README.md)
retains its own positive and negative evidence. It does not replace this
case145 capture or establish complete trajectory repair.
