# ISAC014: actual failed-Q operands and independent saved-arithmetic diagnosis

This packet records a reachable **implementation arithmetic failure**, not a demonstrated paper-formula error. The original Rot-BS & Rot-RIS prefix failed its positive-definiteness guard at rho = 10. The diagnostic process returned 0 because it captured the original failure, not because the optimization succeeded. The original failure is retained.

The original 30,678-byte operand NPZ is copied byte for byte. `original-scenario.json` contains only the named original mathematical constants and solver controls; it is not a complete scene-generator input. The NPZ contains the actual fixed channels, incumbent state, Q/P, original eigensystem and addends needed for these two saved-only readers. Private local path metadata in reports has been projected to stable source labels; no numerical value was edited. Source and input digests distinguish original and public bytes.

## What the actual MP80/MP100 calculations establish

- The positive sensing shift is 3.40546216095828e-9, only 0.028567 of every large diagonal ULP. The stored Q is bitwise equal to its communication addend: the positive shift disappeared during dense addition.
- The actual lower-triangle Hermitian matrix used by `numpy.linalg.eigh(UPLO="L")` has MP minimum eigenvalue -1.39476756748e-7. Merely taking the Hermitian part still gives -6.09373197165e-8. The positive structured original expression has minimum eigenvalue +3.405462160958279e-9. Consequently this is not the rho = 0 theoretical singularity mentioned by the original error string.
- The stored communication P has a spurious nullspace component of 6.9397163e-8, about 68.4 times the actual sensing-P null component. Retaining the original factor form of both Q and P matters; eigenvalue clipping or symmetrization does not recover the original arithmetic.
- At this **one fixed captured subproblem**, the original-formula MP reference has nu = 0 and power 0.388806795523 below the original cap 0.398107170553. MP80 and MP100 primal/dual checks agree. A counterfactual repair of Q alone while retaining rounded dense P instead gives unconstrained power 415.57 and a spurious positive dual multiplier. It is explicitly a diagnostic comparison, not a correction candidate or a production result.
- Total-minus-signal cancellation is quantified separately. It perturbs the positive QT coefficient here, but does not explain negative curvature of the exact positive factor expression.

The complete actual reports are supplied, including the precision scope. The fixed-QCQP reference freezes the captured binary64 coefficients and evaluates their original algebra in MP arithmetic. It does not restore an unrecorded earlier trajectory, prove all future iterates, validate convergence of a corrected implementation, or pass the original-reference/full-paper gate. No correction trajectory was executed by these readers. An equivalent implementation should retain the positive shift and communication/sensing factors separately, solve the unchanged original QCQP and check its original primal/dual residuals; no jitter, clipping or tolerance change is justified by this packet.

## Portable replay

Install Python with NumPy and mpmath. Both commands operate only on saved data, use no RNG, import no optimizer or private core, and require a fresh output directory outside the packet:

```text
python -B diagnose_saved_actual_Q_MP80_MP100_v1.py --output-dir /your/fresh/Q-diagnosis
python -B solve_only_saved_rank1_QCQP_MP80_MP100_v1.py --output-dir /your/fresh/fixed-QCQP
```

Run each script by its package path from any current directory. Their input routes are relative to `__file__`. The second imports the first's pure helpers from this same packet. Their numerical functions and thresholds are identical to those used for the two actual reports; reader1 has only its input-routing header changed and reader2 is byte-identical. Each replay records before/after hashes of all consumed data and reader files. Generated timing and local path metadata may differ; the original numerical fields remain the comparison target.

Both portable readers were actually executed once from a different current directory into fresh directories outside this packet. Both returned exit 0 with closed input/source intervals. Every result field except elapsed time and local source-path metadata exactly reproduced the two original actual reports, including all MP decimal strings and binary64 scalar bits. The included actual first-use receipt binds their output digests. This is saved-data replay, not a new optimization or a correction trajectory.
