# MIS communications: conditional call-17 line-search diagnostic

This records a focused diagnostic of one saved endpoint: Fig. 11 point 0,
start 4869, continuation call 17, with the saved continuation parameter
`mu = 0.0118255615234375`. The recorded stop is
`block_line_search_exhausted_phi`. This is not a rerun of the optimizer or
proof of convergence, physical feasibility, the complete figure, or the paper.

For the current reconstructed model, the diagnostic evaluated the first
iteration's phase-block direction at all 60 original steps `alpha = 2^-j`,
for `j = 0,...,59`. Its binary64 Armijo comparison accepted none. At the same
binary64 candidate points, the 80- and 100-decimal-digit objective differences
also led to rejection of all 60 steps using the same binary64 slope criterion.
All 60 recorded stable binary64 and displayed 100-digit objective differences
are positive. The projected displacement slope is negative in the first 34
trials and nonnegative in the remaining 26. Every candidate differs from the
base point in at least one stored phase bit; this does not establish that all
candidates differ from each other.

The reconstructed projected KKT norm is approximately `1.596e-6`, above
the `1e-6` global tolerance. The phase-block projected-gradient norm is
approximately `1.371e-6`, above its post-exhaustion threshold of about
`5.774e-7`. Under these current-model checks the recorded first-block outcome
is line-search exhaustion. The reported last tested step is `2^-59`; the
smaller `2^-60` is the value after the final rejected step.

The diagnostic uses the same supplied binary64 array factors, fixed other
variables, and binary64 candidate points across precisions; high-precision
comparisons do not independently reconstruct the historical geometry. The
100-digit values are displayed to 65 significant digits, with acceptance
determined before display rounding. High precision is **not** an interval
certificate. The historical execution recorded Python 3.12.14 and NumPy 2.5.3;
the diagnostic used Python 3.12.14, NumPy 2.3.5 and mpmath 1.4.1. Source
digests match saved declarations where reported, but historical production
source, imported dependencies and saved state were not freshly authenticated.
Accordingly, the evidence does not establish the unique cause of rejection,
prove a gradient or paper error, or attribute the failure solely to rounding.

[`recorded_armijo_redacted.json`](recorded_armijo_redacted.json) retains all
60 recorded trial entries and the original diagnostic fields except local
input paths, which were removed for privacy. It is a redacted result projection,
not the original tape, a standalone reproduction, or a verification of the
historical source. The guarded diagnostic exited naturally without exceeding
its observed resource thresholds; polling was not a hard filesystem quota.
