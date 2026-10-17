# Actual full-size ISAC line-search failure

This packet retains the executed failure in original case000/mc045, AO phase
call53, RCG iteration371: M4/N36/K2/A66,6 streams, all physical paths, fixed
W/rotation/iota, previous PR vectors and all80 actual trial vectors. Stored
complex radii are preserved exactly.

The original binary64 evaluator forms interference as total minus desired
signal power. Here signal power932.2074580911001 is combined with interference
about0.001000044787668685. Subtraction loses about8.05e-11 relative accuracy
in that small denominator and corrupts near-stationary objective differences.

At the actual alpha=2^-11 trial, independent full-physics MP80 and MP100 find
an increase of **5.519643719972964e-11**, above the unchanged original Armijo
requirement **1.7222603883046593e-14**. The original evaluator reports a decrease
of2.0239809828126454e-11 and rejects it. Explicit self-excluded interference
summation reports an increase of5.519140700016578e-11 and accepts it. Both
precisions accept69 of the80 stored trials. Their maximum discrepancy across
objectives, analytic gradients and slopes is below7.90e-76 for full physics.
The separate exact-promoted binary64-field lane isolates metric arithmetic
from physical-path rounding.

The direction has positive analytic slope. The full-physics normalized gradient
is9.89841151477324e-5, above the original1e-6 stop. Neither a non-ascent PR
direction nor an already-converged point explains this failure.

The isolated stable provider uses I=noise+sum(other-stream powers), T=I+S,
log1p(S/I), a direct1/T self-gradient coefficient and -S/(T I) other-stream
coefficients. Rotation derivatives explicitly sum other-stream derivatives;
the QT auxiliary uses the same explicit interference sum. These are equivalent
evaluations of the original model, with no changed solver or stopping rule.

Independent MP80/100 checks cover all24 complex W gradients,36 complex RIS
gradients and6 rotation derivatives. Maximum errors are3.36e-9,4.26e-11 and
4.38e-9, below the existing component-test absolute1e-5 bound. W/RIS references
are analytic; rotation uses an independent MP central difference at1e-20.
The component bound is not a solver stopping tolerance.

Continuation preserves the previous PR vectors and uses only the129 iterations
remaining in the original500 budget. It passes the failed step without another
Armijo exception, but ends at normalized gradient8.945971764733584e-5:
**still unconverged**. This mixed-prefix suffix is not a cold phase or complete
six-scheme result. A separate full cold six-scheme case is pending. The active
original batch and all original strict source files remain unchanged.

Install `strict/requirements.txt` and `mpmath==1.4.1`; use fresh destinations:

```text
python tools/isac-line-search-replay/audit_failure.py --capture strict/validation/isac045-actual-line-search-20261017 --output-dir new-actual80-MP-audit
python tools/isac-line-search-replay/audit_stable_derivatives.py --capture strict/validation/isac045-actual-line-search-20261017 --output new-all-gradient-audit.json
python tools/isac-line-search-replay/continue_phase.py --capture strict/validation/isac045-actual-line-search-20261017 --output-dir new-original-budget-continuation
```

The manifest binds every payload. The archive retains all four complete
MP lanes. The unchanged independent physical oracle SHA256 is
d14050078d636ca33bd78fb2206406735a22589eeb0aa14b0f28c3d443d893bc.
The cold adapter reads original source into a private module and records a
distinct source binding. No manuscript or private path is included. Full
convergence, MATLAB agreement and original curves remain open.
