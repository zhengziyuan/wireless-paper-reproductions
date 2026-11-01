# MIS communications: conditional continuous-path diagnosis

This static evidence concerns the saved Fig. 11 point 0, start 4869, call 17
endpoint. The original recorded stop was `block_line_search_exhausted_phi`.
The analysis uses the current reconstructed model and the same supplied
binary64 array factors, saved state, and first-iteration direction. It does not
rerun the optimizer, authenticate the historical producer or state, or prove
convergence or an error in the paper.

For each of the original 60 step sizes \(\alpha=2^{-j}\), \(j=0,\ldots,59\),
the guarded diagnostic compared a high-precision continuous normalization
path against the binary64 candidate. Both 80- and 100-digit calculations are
reported; they are not certified intervals. The precise model inputs and
calculation are conditional on the saved values and current implementation.

The continuous path uses \(p(\alpha)=\operatorname{normalize}(\phi+\alpha d)\).
Its normalized base \(p(0)\) has an objective about \(2.6820\times10^{-15}\)
higher than the saved binary64 base \(\phi\); its initial derivative is about
\(-1.8802\times10^{-12}\). Relative to the normalized base, steps 0–8 increase
the objective and steps 9–59 decrease it; the first decrease occurs at
\(\alpha=2^{-9}\), approximately \(-4.4619\times10^{-16}\). Relative to the
saved base, every continuous candidate and every high-precision re-evaluation
of a binary64 candidate has a positive objective difference. These are two
different baselines and should not be conflated.

The maximum absolute objective difference between a binary64 candidate and
its paired continuous candidate is approximately \(2.954\times10^{-15}\).
These observations show sensitivity at this point, but do not establish the
sole cause of the historical failure or warrant changing the original method.
The separately published [60-step binary64/MP Armijo diagnosis](../mis-communications-call17-evidence-v1/README.md)
reports the actual candidate criterion. The ideal continuous-path derivative
test in this record is not the engine's actual binary64 Armijo decision.

The saved run recorded NumPy 2.5.3, while this diagnostic used NumPy 2.3.5;
source and dependency histories were not fully authenticated. Individual input
reads were locked, but historical content and a whole-event atomic snapshot
were not reauthenticated. The task naturally exited with code 0 under the
existing storage/time guard; polling is not a hard filesystem quota.

[`recorded_continuous_redacted.json`](recorded_continuous_redacted.json) is a
static projection of the actual result: only the `source_input_paths` field
was removed to avoid publishing local paths. All remaining data are retained.
This package is evidence of the recorded diagnostic, not a standalone replay
of the original experiment.
