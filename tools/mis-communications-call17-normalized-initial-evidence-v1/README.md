# MIS communications: normalized-initialization single-block diagnosis

This static record concerns the saved Fig. 11 point 0, start 4869, call 17.
Its recorded stop was `block_line_search_exhausted_phi`. A bounded diagnostic
made **one binary64 zero-step phi retraction** on that saved state, recomputed
the objective and gradient, and evaluated the reconstructed implementation's
guarded first-block Armijo rule (`original_per_block_backtracking`, with its
`documented_non_descent_restart` policy and actual-displacement slope) on the
60 step sizes \(2^{-j}\), \(j=0,\ldots,59\). This is a
modified starting state and a reconstructed diagnostic, not a rerun or a
verified fix of the original optimization. The stored failure remains intact.

The zero-step retraction changed 44 real/imaginary binary64 components, with
maximum complex-coordinate change about \(2.483\times10^{-16}\). Applying
the same zero-step retraction a second time was **not bitwise idempotent**;
neither outcome establishes exact unit modulus in real arithmetic. At 80 and
100 decimal digits, the objective of the new binary64 base minus that of the
saved base was approximately \(+9.428909532249626\times10^{-16}\). Both
evaluations use the current supplied binary64 array factors. The saved and
new-base projected KKT measures were approximately \(1.5959605004\times10^{-6}\)
and \(1.5959628107\times10^{-6}\), respectively, against the retained
\(10^{-6}\) stopping tolerance.

The first accepted binary64 first-block candidate was \(j=9\),
\(\alpha=2^{-9}=0.001953125\). Its displacement slope was approximately
\(-3.6723365451\times10^{-15}\); its retained Armijo right-hand side was
\(-3.6723365451\times10^{-19}\), and the binary64 stable objective difference
relative to the **new base** was approximately \(-1.0911286262\times10^{-15}\).
Re-evaluating the same binary64 candidate at 80 and 100 digits gave approximately
\(-1.091127041763985\times10^{-15}\) relative to that new base. Adding the
recorded normalization offset yields approximately
\(-1.482360885390220\times10^{-16}\) relative to the **saved base**; this last
number is arithmetic on displayed, rounded MP values. The MP acceptance check
uses the binary64 displacement slope, and neither precision is an interval
certificate.

All 60 candidates are reported as an offline counterfactual comparison. In the
reconstructed first-block search, candidates after the first accepted one
would not be tried; if the global KKT test had already passed, the search would
not start. An accepted first block is not an accepted joint step, a converged
optimizer, a complete figure, a MATLAB/Python validation, or agreement with
the paper. The observation supports investigation of the local floating-point
initialization; it does not establish the sole cause of the historical stop or
prove that normalization fixes it globally.

The previous [continuous-path diagnosis](../mis-communications-call17-continuous-evidence-v1/README.md)
considered ideal high-precision normalization of the saved binary64 state; its
\(+2.6820\times10^{-15}\) base offset is for that ideal base, not the new
binary64-retracted base above. The prior [60-step saved-base Armijo diagnosis](../mis-communications-call17-evidence-v1/README.md)
also remains available. These records use different base points and must not be
interchanged.

The saved runtime recorded NumPy 2.5.3; the reconstruction used NumPy 2.3.5
and mpmath 1.4.1. The current engine and figure data matched recorded manifest
digests, and individual inputs were held during reads. The historical producer,
complete dependency history, and whole-event atomic snapshot were not fully
authenticated; current imported packages were not fully authenticated either.
The calculation is conditional on the available state, source, and binary64
factors and does not establish a paper error.

The one-child guarded task exited naturally with code 0 after about 4.109 s;
the recorded minimum free space was 139,761,405,952 bytes (about 130.163 GiB),
and its output tree held 42,422 bytes before the terminal receipt. It retained
the 600 s limit, 900 KiB early output threshold, 1 MiB nominal output bound,
101 GiB early free-space threshold, and one-second polling. Polling is not a
hard filesystem quota; successful resource and structure checks are not
scientific acceptance.

[`recorded_normalized_initial_redacted.json`](recorded_normalized_initial_redacted.json)
contains the recorded diagnostic with its machine-local input paths removed,
the derived saved-base comparison, and the resource terminal record. It does
not include endpoint arrays and is not a standalone replay.
