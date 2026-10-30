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

`verify_zf_feasible_improvement.py --job JOB.json --config CONFIG.json
--result RESULT.json` checks one specific saved Fig. 5 ZF endpoint and an
explicit nearby antenna position. For the case-007/mc-000 record, the new
point satisfies box and spacing comparisons over the exact stored binary64
numbers, and the floating-point statistical objective increases by about
0.00033353 bit/s/Hz. The saved last-sweep relative gain is below its configured
stopping threshold, so the point does not contradict that finite stopping rule.
It is not proof of a paper error, a global optimum gap, physical feasibility
under uncertain inputs, or full-figure reproduction.
