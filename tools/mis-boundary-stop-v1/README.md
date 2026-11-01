# MIS zero-motion stopping-reason correction

This isolated correction addresses a reconstruction reporting defect, not a
demonstrated error in the paper. In the original Python and MATLAB engines,
the per-block line search uses the projected KKT norm when all blocks have
zero projected motion, even for the `literal_printed` policy whose stated
stopping norm is the row-mean gradient norm. At the simplex boundary, the
two norms can differ. Consequently a stop may be labelled
`gradient_tolerance` although the selected literal norm exceeds tolerance.
The separate Python population summary already checks its selected norm; no
full-population false-success claim follows from this example.

`boundary_stop_v1.run_rcg` binds a copy of the original Python RCG function's
global namespace and wraps only its block-search exit reason. The untouched
source is `strict/mis-communications/engine.py`, SHA-256
`eb90ca857df1cf3aed094c91c1ccee1461e571a96f15e42f7545768acaa1de77`.
The adapter changes the reason to `zero_projected_PR_direction` only when the
literal policy otherwise claims gradient tolerance and its row-mean norm still
exceeds the configured tolerance. Iterates, search, evaluations, returned
metrics, and budget are unchanged. The caller must verify the frozen source
identity before use; this adapter is not connected to an existing production
run and does not validate a figure. A policy other than the two named policies
is rejected before evaluating the objective; an absent policy retains the
original default `literal_printed`.

The corresponding MATLAB change is **local static preparation only**; this
Python-only release does not include a runtime-verified MATLAB variant. A
MATLAB self-test was launched without the required external storage guard and
stopped; no MATLAB test success is claimed. Its record and retained temporary
files remain in the local data tree. The unmodified original MATLAB engine has
SHA-256 `763a55bbcd74561c56f4bf668ef634863546b2cf235d16ab1854102d32da2108`.

The Python synthetic tests use the minimization objective `-X[0]+X[1]` on
the simplex at `[1,0]`: row-mean norm `sqrt(2)` and projected KKT residual
zero. This is a valid boundary optimum. The test checks stop reporting, not
optimality, complete convergence, a published scenario, cross-language
agreement, or original-figure accuracy.

Run the small checks from this directory with `python -B test_boundary_stop_v1.py`.
