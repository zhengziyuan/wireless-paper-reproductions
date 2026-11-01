# Saved ISAC004 sensing and total rotation-gradient check

This diagnostic replays one saved intermediate state from the Rot-BS / No-RIS
failure, realization 4, with the beamformer and previously captured scaling
parameter fixed. It checks three BS rotation derivatives. It does not run an
optimizer, generate random channels, resume the failed run, or establish full
feasibility, convergence, MATLAB/Python agreement or paper-figure reproduction.
See the [related communication gradient evidence](../isac004-boundary-rate-gradient-v1/README.md)
and [original failure evidence](../isac004-paper19-saved-state-v1/README.md).

The fixture contains only required parameters and selected saved binary64 arrays.
Local checks bound those arrays to the retained failure-state capture and found
that the current workspace source reconstructs the saved field and Jacobian
exactly; this package by itself cannot prove the capture provenance or the source
actually loaded by the historical process. All saved BS-RIS path gains are zero;
the direct-only model therefore covers this No-RIS state, not nonzero RIS cases.

For [arXiv:2512.20987v2](https://arxiv.org/html/2512.20987v2), Eq. (22) and
its weighted objective, the script reconstructs the rate and sensing pattern in
50-digit Decimal arithmetic from the saved binary64 geometry, gains and Python
binary64 wavenumber. It compares central differences with the gradient evaluated
from the saved field/Jacobian. At step 1e-10, the largest absolute discrepancy is
about 1.60e-22 for the weighted sensing term and 9.23e-15 for total utility.
The closest communication and target directional cosines are approximately
3.76e-9 and 0.0153, respectively. For this state and step, the bound on the
rotation derivative of each direction cosine excludes a half-space crossing.
Larger finite differences may cross the communication boundary and mislead.

This is a fixed-state numerical diagnostic, not a proof for all cases, nor a
claim about an author-selected epsilon. It uses the previously captured finite
scale, whose numerical value is retained in the fixture. The original zero-
overlap failure remains unresolved. Binary64 model inputs and Decimal finite
differences do not recover exact physical geometry.

Run with Python 3 and NumPy, providing a new output path:

```text
python -B replay.py --input-dir . --output /path/to/new-result.json
```
