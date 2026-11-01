# Structured solve of the one captured ISAC014 QCQP

This is a minimal supplement to the parent failed-Q arithmetic evidence. It contains the **actual Python and MATLAB fixed-subproblem implementations**, their exact captured input, actual returned arrays and the completed independent MP80/MP100 comparison. Both mathematical source files are copied whole byte for byte from those actually executed. It is an equivalent numerical representation of the original positive-alpha QCQP, not a new objective, a paper-formula correction or a complete optimization trajectory.

The solver retains Q = alpha I + B B^H and the communication part of P in the same factor basis. Alpha and sensing coordinates are retained separately. It does not use the failed dense Q or the rounded assembled communication P, introduce diagonal loading, clip eigenvalues, impose a numerical rank threshold or change the original bisection tolerance. The only zero-weight branch tests eta == 0 exactly. The validated domain is finite positive alpha/rho, nonnegative mu and K <= M; this packet verifies the actual captured M=4, K=2, six-stream case.

## Actual outcome and precision boundary

Both implementations actually returned nu = 0 with the original power cap 0.3981071705534972. MP evaluation of their saved W gives power 0.388806795522997155 (Python) and 0.388806795522997243 (MATLAB), versus the original-formula MP reference 0.388806795522997410. Maximum component error is about 1.51436e-16; the cross-language maximum component difference is about 1.00074e-16. These are close numerical solutions, not bitwise-identical outputs.

The **absolute** original-formula stationarity residuals are approximately **4.757685279e-7 (Python)** and **2.854038772e-7 (MATLAB)**. They are not hidden or described as passing a 1e-7 absolute residual cutoff. The original source has no such QCQP residual stopping cutoff. On the disclosed original QW/P scale, the corresponding relative residuals are approximately **3.983760054e-16** and **2.389776747e-16**. Power feasibility, nonnegative dual variable, zero complementarity, original fixed-iota physical non-decrease and the unused-nu0 bracket semantics were checked. The independent comparison additionally used the disclosed 1e-7 scene verification tolerance for solution/QCQP/physical-reference comparisons; this is an explicit comparison bound, not a changed production stop rule.

The full actual validation report preserves both MP precision lanes, every original/added check and these residual values. The process closure alone is not scientific acceptance. The first host attempt failed during MAT export because unused nu0 brackets were Python None; native execution had not begun. That actual exit 1 remains recorded. The subsequent V2 projected only unused None to MAT empty arrays (JSON null), with a raw array backup first, while leaving both numerical implementations unchanged.

## Files and input semantics

- `exact-captured-fixed-subproblem.mat` is the exact 2,256-byte MAT file used for the actual native solve. Its bytes are unchanged.
- `exact-captured-fixed-subproblem.npz` is a pure transport of the same actual Python call's ten inputs. Arrays preserve their Python semantic shape and every real/imaginary binary64 bit. The MAT/NPZ numerical values and shape mapping were checked without running a solver.
- `actual-python-fixed-qcqp.mat`, `actual-matlab-fixed-qcqp.mat` and the original Python NPZ array backup are unchanged actual returns.
- The larger original failed operands and independent original-formula MP reference readers are in the parent evidence directory. This supplement does not duplicate them.

Only local path metadata in JSON evidence was projected to source labels. Numerical scalars, arrays and MP decimal strings were not edited. `MANIFEST.json` binds this supplement's public file bytes.

## Commands for the fixed subproblem

These are direct calls to the already tested exact mathematical sources, with package-relative inputs. No new package runner was introduced, and these relative command examples were **not rerun after packaging**. They are instructions for a future fresh fixed-subproblem replay, not a claim of another portable first use. Use fresh output paths.

Python (NumPy only), from this directory:

```python
import numpy as np
from structured_original_qcqp_candidate_v1 import solve_fixed_original_qcqp
with np.load('exact-captured-fixed-subproblem.npz', allow_pickle=False) as z:
    inputs = {name: z[name] for name in z.files}
W, diagnostics = solve_fixed_original_qcqp(**inputs)
np.savez('/your/fresh/fixed-result.npz', solution=W)
print(diagnostics['nu'], diagnostics['actual_binary64_power'])
```

MATLAB, with this directory on the MATLAB path:

```matlab
result = solve_fixed_original_qcqp_matlab_v1( ...
    'exact-captured-fixed-subproblem.mat', '/your/fresh/fixed-result.mat');
```

These fixed-subproblem functions perform a QCQP solve only. They perform no outer AO/RCG/PGA trajectory, channel generation, MC sampling or RNG calls. The full original-budget first-scheme arithmetic variant and any later saved-state audit have separate evidence and are not passed by this packet. The original failed result, original-reference discrepancy and full-paper gates remain retained.
