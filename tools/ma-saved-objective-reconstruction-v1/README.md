# Saved objective reconstruction

`verify_saved_objectives.py --job JOB.json --result RESULT.json` checks the
saved MRT and ZF sweep-boundary objectives using independent algebraic
representations, with the existing scenario builder's unit wavelength,
noise and path-gain assumptions. It reads the specified files and prints a
small JSON report; it does not modify the files or execute an optimizer.

The supplied job and result are not authenticated merely because their
metadata agree. This component does not verify intermediate coordinate steps,
Monte Carlo rates, feasibility, mathematical convergence, the MATLAB version,
or published figures. The numerical comparisons are not interval proofs.
