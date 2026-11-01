# Saved ISAC004 near-horizon rate-gradient check

This replays **one intermediate state from the Rot-BS / No-RIS failure** for
realization 4. The selected arrays retain their saved binary64 values; no
optimizer, random sample, MATLAB process, or trajectory is run. The earlier
[saved-state and paper-expansion evidence](../isac004-paper19-saved-state-v1/README.md)
describes the original zero-overlap failure. This fixture alone does not prove
its provenance or that the original run completed.

The communication model uses the rotation-aware paths and half-space element
response of [arXiv:2512.20987v2](https://arxiv.org/html/2512.20987v2),
Eqs. (1)–(12). The `fc` and `jac_comm_rotation` arrays were selected from the
saved field and its rotation Jacobian; `w`, rotations, path geometry, gains,
and noise are likewise selected from the captured state. The local review found
these arrays equal to the corresponding saved operands and reconstructed the
full saved field and Jacobian from the then-current Python implementation.
That local source-to-capture comparison is not reproduced by this portable
package; this replay instead reconstructs the two communication channels from
the selected parameters and compares the resulting channels with `fc`.

The nearest BS-user path has directional cosine approximately
`3.7603115402e-9`. A central step of `1e-4` in the first two rotation angles
crosses the half-space boundary; its difference quotients need not approach
the derivative of the active branch at the saved point. At step `1e-10`, none
of the three coordinate differences crosses a BS-user path boundary. The
50-digit Decimal recomputation gives absolute differences from the rate
gradient derived from the saved Jacobian of approximately `2.23e-15`,
`3.20e-15`, and `9.23e-15`, respectively. The Decimal calculation treats
the saved floating-point inputs and the Python binary64 wavenumber as its
inputs; it does not recover the unknowable exact physical values.

The communication gradient comparison does not check the sensing term,
gradient behavior exactly on the boundary, nonlinear solver feasibility,
convergence, MATLAB/Python agreement, the full published scenarios, or
agreement with the paper's figures. Crossing the boundary is **not** evidence
of a paper error. The separate zero-overlap failure remains unresolved.

With Python 3 and NumPy installed, run with a **new, nonexistent** output
file. No source or existing output is overwritten:

```text
python -B replay.py --input-dir . --output /path/to/new-result.json
```
