# Independent Python audit of recorded stopping evidence

The existing hotspot statistical implementation uses a signed relative
objective increment as a stopping expression. A negative increment can satisfy
that expression, and the existing receipt validation can also accept a
negative value reported as a gradient norm. The included synthetic tests
demonstrate both behaviors against the existing Python production functions.
They do **not** establish that any historical scientific trajectory actually
contained a decrease or an invalid gradient norm.

`audit_saved_history.py` leaves the production implementation, stopping
behavior, iteration budgets and historical checkpoints unchanged. It reports
the production signed stopping expression and separately checks all supplied
recorded increments. Any witnessed negative difference fails the strict
recorded-nondecrease gate, including decreases below the default 1e-6 absolute
numerical diagnostic tolerance. A small decrease is counted separately; it is
not automatically interpreted as a physical violation. An incomplete history
cannot pass the gate even if it contains no negative increment. The caller's
`complete` Boolean is an assertion about the supplied history, not evidence
that its provenance is authentic or no iteration was omitted. The gradient
audit independently requires the reported norm to be nonnegative.

For an empty or singleton history, `production_signed_stop_recomputed` is
`None`: there is no expression to compute. The existing production receipt's
`converged` field is instead `false` for those cases. `None` for an independent
gate means the evidence supplied to that gate is insufficient.

The new audit has **not** been integrated into the production runner and has
not been applied to any real scientific trajectory as part of these synthetic
tests. Its nonnegative-step result is not a proof of mathematical convergence,
source identity, feasibility, MATLAB agreement or full reproduction. A MATLAB
counterpart and its controlled runtime verification remain pending.

From the repository root, run the synthetic regression with Python 3 and NumPy
installed:

```text
python -I -B tools/hotspot-recorded-history-audit-python-v1/test_saved_history.py
```

The test compares the new interpretation with existing
`strict/hotspot-satcom/termination.py` on finite toy inputs; it neither starts
an optimization nor reads a saved scientific trajectory.
