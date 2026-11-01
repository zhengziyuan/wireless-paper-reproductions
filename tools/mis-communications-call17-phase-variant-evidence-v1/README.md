# MIS communications: experimental phase retraction for one saved start

This record covers Fig. 11 point 0, start 4869, call 17, **one reconstructed
start only**. It starts at iteration 0 from the binary64 normalized state
immediately before the earlier joint step. The earlier conditional continuation
starts at iteration 1, after that different joint step; its first cursor is thus
not the same state as this experiment's first cursor. The boundary contains a
`direction_inference` object from validating that earlier joint-step receipt;
it is provenance metadata and is **not** used as the variant's initial
direction: the encoded variant state has iteration 0 and null old gradient
and direction.

The experiment changes only the in-memory implementation of phase retraction.
On an exactly unit-modulus complex input the variant is algebraically equal to
the affine normalization used by the reconstructed engine. Stored binary64
phases are not exactly unit modulus; the new calculation approximately retains
their existing radii and follows a different floating-point path. The existing
projection formula assumes exact unit modulus. This is a numerical experiment,
not the authenticated author implementation or a proven equivalent finite
precision trajectory. The original run and failure records remain intact.

It keeps the reconstructed implementation's actual-candidate displacement
Armijo tests, settings (60 trials per backtracking loop, 4000 inner iterations
per μ and 1e-6 projected KKT tolerance), and the remaining μ schedule. These
are documented **implementation settings**, not a claim that the paper itself
specified those numerical values. The existing joint-coupling safeguard is a
disclosed reconstructed-implementation choice. The method does not run or
validate MATLAB; a MATLAB candidate exists but has not been executed here.

| μ | experimental stop | projected KKT | prior conditional stop | prior KKT |
|---:|---|---:|---|---:|
| 0.0118255615234375 | gradient_tolerance | 4.96748325481e-07 | gradient_tolerance | 6.75782074912e-07 |
| 0.00591278076171875 | gradient_tolerance | 7.93033464157e-07 | gradient_tolerance | 5.79363863138e-07 |
| 0.002956390380859375 | gradient_tolerance | 4.19068109755e-07 | block_line_search_exhausted_phi | 2.45516528417e-06 |
| 0.0014781951904296875 | gradient_tolerance | 4.80036544143e-07 | block_line_search_exhausted_phi | 4.80667063003e-06 |

The experiment records 10 RCG checks/iterations; final selected binary
and relaxed minimum SINR are 35.624058442737 in the implementation's units. The prior
conditional result was 35.624058441059; the difference is 1.67822e-09, and the saved
binary schedules agree: true. These values are neither
a 6000-start ranking nor original-paper agreement. Because the variant also
executes a new first joint step, the prior continuation's direction was inferred,
and the historical state is not authenticated, this comparison does not
establish a unique cause for the different stops.
Prior original/conditional
failures are not erased, and the successful KKT stops do not establish global
convergence or correctness of every scenario.

Per-iteration monitoring measured a maximum returned phase radial deviation of
4.44089e-16 and maximum over finite attempted candidates of
4.44089e-16, using binary64 `abs`; these are observations, not
interval-certified feasibility bounds. The events include actual maximum
rounded phase displacements, zero-displacement and nonfinite counts. Only the
returned rounded candidate is passed to the retained Armijo test.

The E-volume guard returned naturally with 142896
bytes before its terminal record; it uses polling, not a hard filesystem quota.
Historical loaded source and all dependencies were not reauthenticated. The
full six-paper MATLAB/Python, feasibility, original-figure and reference gates
remain incomplete; no paper-level pass is asserted.
