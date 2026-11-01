# Numerical admission boundaries for the corrected hotspot QT block

`counterexamples.py` uses exact rational arithmetic for two deliberately
constructed inputs. It does not run CVX, CVXPY, MATLAB, an optimizer, or a
paper scenario, and it reads and writes no files.

1. For a full-rank two-dimensional covariance, a **hypothetical** solver
   candidate satisfies the corrected full-interference QoS and power bounds and increases the HU
   objective, while violating the fixed-auxiliary QoS lower-bound constraint
   of the repository's corrected QT subproblem. The existing Python candidate
   acceptance predicate checks the former quantities but does not include this
   lower-bound constraint. Its later `solver_diagnostics`/`scheme_status`
   machinery can record a constraint violation and fail the final scheme gate;
   the counterexample concerns internal candidate acceptance only and does not
   establish that the final gate would pass. It does not show that any solver
   returned this candidate or that any stored run violated its subproblem.
2. Both historical factor routines use a negative-eigenvalue threshold scaled
   by `max(1,max(abs(eigenvalues)))`, followed by clipping negative eigenvalues.
   A deliberately invalid, weak-scale matrix can pass that check while the
   relative size of its clipped part is close to one. This does not establish
   that any saved physical covariance is indefinite or was changed.

The mathematically exact QT lower bound remains valid, including every other
transmitted stream. The paper's printed statistical denominator omits HU
interference; the signal-model correction includes it and is separately
documented in `strict/hotspot-satcom/STATISTICAL_ERRATUM.md`. This is an
independently disclosed correction to the
paper's invalid printed conic replacement, not proof of the author's historical
algorithm. Safe future use requires checking the fixed-auxiliary constraints,
full-interference QoS and power, objective, factorization error and declared numerical
tolerances; failure must preserve the previous state and evidence. The existing
frozen source and results remain unchanged. No full-paper acceptance follows.

Run `python -B counterexamples.py`.

`candidate_guard.py` is a separate, versioned, **unintegrated** numerical
review of an old and candidate beamformer. It independently checks covariance
factorization, finite/Hermitian/PSD input, old feasibility and tightness,
fixed-old-auxiliary QoS lower bounds, candidate true QoS, power and HU rate.
True QoS uses the supplied moments, while the auxiliary and fixed bound use
the supplied actual factors separately. Interference sums the other streams
directly, avoiding cancellation from subtracting a large desired signal.
Every HU lower bound must lie strictly inside the logarithm's domain, and the
fixed-auxiliary surrogate sum rate is separately compared to its old value with
the caller's explicit tolerance. This is distinct from comparing the true rate.
Every individual computed receive power must be nonnegative, with a strict zero
threshold in its physical power units. This conservative rule may reject a
genuinely positive-semidefinite input if floating-point roundoff makes a tiny
quadratic value negative; it does not silently clip or relax that value.
It accepts explicit tolerances and reports them; it never writes inputs or
changes an old beamformer. `test_candidate_guard.py` exercises small in-memory
cases. The guard is not connected to the historical Python or MATLAB loop:
actual use needs reviewed integration, source/input binding, both-language
execution and the existing storage guard. It does not certify a paper result.
