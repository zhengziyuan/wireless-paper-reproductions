# Saved ISAC004 fixed-scale W gradient

This checks all 48 real components of the complex beamformer at one retained
Rot-BS / No-RIS failure state. It reuses the compact fixture from the adjacent
[sensing rotation-gradient evidence](../isac004-boundary-sensing-total-gradient-v1/README.md);
no second set of numerical inputs is stored. The fixed scaling value comes
from the retained call stack. The analytic gradient is reconstructed from the
current implementation's formula and compared with centered differences of an
independently summed interference objective. The perturbations are unconstrained
and are not feasible-iterate or optimization evidence.

At steps 1e-4, 1e-5 and 1e-6 the maximum absolute differences over 48
components are approximately 4.90e-7, 4.97e-9 and 3.36e-9. The script uses
binary64 arithmetic; these are numerical checks, not interval guarantees.
The original failure remains unresolved; the historical process's loaded code,
MATLAB, convergence, physical feasibility and full figures are not verified.

From this directory, with Python 3 and NumPy, use a new output path:

```text
python -B replay.py --input-dir ../isac004-boundary-sensing-total-gradient-v1 --output /path/to/new-output.json
```
