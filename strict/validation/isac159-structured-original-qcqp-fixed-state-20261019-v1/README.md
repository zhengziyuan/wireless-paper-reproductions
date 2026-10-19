# Structured original QCQP candidate: one captured failed ISAC subproblem

This package preserves and diagnoses one real failed-Q boundary in original case159, then validates an isolated numerical representation of the same theoretical QCQP. It contains the original30KB operand capture, both actual candidate sources and outputs, and losslessly compressed independent MP80/MP100 references. It is not a full scheme or scenario rerun and does not install a change into any live core.

The original input had rho10. Its stored Q is not exactly Hermitian; the original NumPy eigh uses the lower triangle with a real diagonal. That exact lower-Hermitian input has MP minimum -5.48763e-8, while the same-auxiliary theoretical Gram+alphaI has minimum +4.81710e-8 and condition about4.44e16. The captured large communication P also has a1.46447e-7 spurious null-space component; dividing it by the original alpha+nu gives about2.99. Merely replacing the Q eigensolver while continuing to project the rounded communication P is therefore inadequate.

For the candidate, A=Fc diag(sqrt(1+mu)|eta|/sqrt(log2)) and Q=A AH+the original alphaI. The communication P is A G, with G's nonzero diagonal sqrt(1+mu)eta/(sqrt(log2)|eta|), padded with the original zero columns. Its SVD coordinates are Sigma VH G; no assembled large communication P is projected into a numerical null space. Sensing coordinates retain alpha LHW-rho LHGa/(2D). Only exact eta0 terms are zeroed by their exact formula; there is no rank cutoff, negative eigenvalue clamp, jitter or fitted regularization. The original positive alpha is retained.

The scalar nu control is unchanged: lo0/hi1, original doubling if needed, original bisection stop hi-lo<=tol*max(1,hi), and selection of hi. Both actual languages and both reference tiers select nu7.60337570682168e-10 with40 bisections and0 doublings. The complete MP control traces are included. Actual candidates serialized their final interval and count; these endpoints and40 dyadic cuts determine the same branch path. Intermediate candidate power values were not separately taped.

Actual results passed the scoped fixed-subproblem comparison. Against A, W maximum errors were1.685e-16(Python) and9.063e-17(MATLAB); against B they were7.164e-15 and7.096e-15. Cross-language W difference was1.144e-16. Power was about0.6309544294, below the original0.6309573445 cap; original physical utility increased about3.97054e-9. QCQP objective errors were at most4.58e-23. Absolute stationarity residuals ranged3.35e-8..3.13e-7; relative backward residuals ranged2.13e-17..1.99e-16. The original code records this residual without an absolute pass cutoff: these numbers are diagnostics, not a new or relaxed stopping rule.

Reference A evaluates the original structure with exact promoted captured auxiliaries. Reference B independently recomputes physical fields and auxiliaries at the same W/theta/rotation/iota. They are separate subproblems: their Q/P and surrogate objective scales differ, though solved W differs only7.17e-15. The stored indefinite Q or polluted P is never used as a theoretical solution reference. Added W/objective/physical-utility comparisons use the disclosed scene verification tolerance1e-7; that comparison does not alter the original algorithm or bisection stop.

## Portable checks using only existing data

Python, NumPy, SciPy and mpmath are needed. From this package root, choose a fresh output directory outside the package:

```console
python check_fixed_subproblem.py --output-dir ../fixed-qcqp-recorded-check
```

This checks both stored actual candidate outputs against the supplied reference numbers. It does not recalculate a high-precision solution or channel oracle. To also execute one Python fixed-QCQP solve on the same captured data:

```console
python check_fixed_subproblem.py --solve-python --output-dir ../fixed-qcqp-python-check
```

For a fresh native fixed solve with an installed MATLAB, use the existing typed fixture and a fresh external output:

```matlab
addpath('sources');
solve_fixed_original_qcqp_matlab_v1('data/exact-captured-fixed-subproblem.mat','../fresh-native-fixed-qcqp.mat');
```

Then compare its numerical output:

```console
python check_fixed_subproblem.py --native-result ../fresh-native-fixed-qcqp.mat --output-dir ../fixed-qcqp-native-check
```

An externally supplied result file alone does not certify its producer's source or input identity; the command above states the intended fixture. The published actual source/input closure is separate. Actual relative-layout first use is now closed: the fresh Python fixed solve/check, fresh native fixed solve, and native numeric comparison all naturally returned 0 with original handle/source/input closure. Both numerical checks passed against the existing MP80/MP100 references. The receipts and fresh native output are in results/portable-*. No MP reference solve, trajectory or Monte Carlo experiment was repeated. Only this fixed subproblem was exercised.

## Failures and limits retained

The original bad Q/P, original failed guard and source context are retained. The previous three-state arithmetic package's expanded intermediate gate remains false and its original Python process exit1 remains recorded; this different single-QCQP result does not clear that gate. New host failures are also retained separately: a SciPy31-character struct-field limit, and a new fixture accidentally transporting rho as int64. The corrected fixture uses double10, as original MATLAB jsondecode does. These were new transportation errors, not failures in old native production or the earlier public18-file package.

Only this M4/K2/six-stream state with finite nonnegative mu, K<=M and original alpha>0 has been validated. Alpha0/rho0, negative-mu inputs, other dimensions and complete trajectories are outside this evidence. There is no full convergence, optimized-state dual equality, original-paper curve agreement or whole-paper PASS claim. All old failed data and live sources remain unchanged.

`sources/historical_original_core.py` is an exact original source witness, not the corrected entry. Use `check_fixed_subproblem.py` for this limited package. `manifest.json` binds every file except itself; reference gzip decompression restores exact original JSON bytes. Local `.gitattributes` preserves bytes.
