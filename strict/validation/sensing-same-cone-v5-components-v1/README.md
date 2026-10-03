# Same-projection v5 component and cold-start evidence

This folder publishes the complete exact-byte scientific v5 code/configuration
and the compact evidence for the actual projection correction. It is **not** a
completed 6000-start figure or an original-author implementation.

The correction changes only the numeric evaluation of the same Euclidean
closed-simplex tangent cone; original model, raw product-PR branch, initialization,
accepted-line tests, 6000 population, 30 outer and 4000 inner budgets are retained.
See `NUMERICAL_FIX_SCOPE.md` for the finite-root proof and explicit algorithm
scope. The published corrected-product branch remains distinct from the paper's
printed separate-block branch; no source-theory distinction is erased.

Actual native MATLAB and Python both passed 1025 projection tests and their own
complete cold start 377. The final physical KKT/constraints were independently
recomputed at Decimal60, separately from the thirty actual inner stopping gates.
The native and Python eta values differ (48.9905312 versus43.6907272): these are
different nonconvex floating trajectories, not alleged bitwise/curve agreement.

The compact full-start receipt includes every actual outer stop plus the final
state and lists the original complete receipt hashes. Native interval bindings
retain all46 exact source/input hashes. Their relative paths are portable, but
copying files is not a new native execution on the reader's device.

## Native component or one original full-budget cold start

From this folder in MATLAB:

```matlab
maxNumCompThreads(1);
run_sensing_v5_native_bound('cone-component','my-component.json','my-component-binding.json','native-v5-expected-binding.json');
run_sensing_v5_native_bound('full-start377','my-cold377.json','my-cold377-binding.json','native-v5-expected-binding.json');
```

Use fresh output paths. The component wrapper enforces the selected function
and frozen source/input hashes before and after each actual run.

## New complete Python population

Install Python+NumPy as documented by the repository. From this folder:

```text
python execute_sensing_v5.py --figure fig3 --bank my-new-full6000-bank --workers 2
```

This performs a NEW complete6000 population; it does not reuse historical passed
starts. Numerical exceptions are retained as failed-start gzip records and do
not silently stop the remaining population. A failed inner/capped start remains
failed even if its final KKT happens to pass. No exception can contribute a fake
mean or verified incumbent. Completing the population does not guarantee every
original4000-budget solve converges or prove global optimality/author-figure fit.

The historical incomplete v4 bank and all36 capped/unverified records remain
preserved in the separate `sensing-correctness-v4/failed-bank-v4-v1` proof.
