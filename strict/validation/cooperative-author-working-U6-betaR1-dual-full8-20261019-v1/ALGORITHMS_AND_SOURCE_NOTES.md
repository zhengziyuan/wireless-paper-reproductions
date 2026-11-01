# Source discrepancies and the implementation correction

## Four diagnosed printed algebraic inconsistencies

These are independently checked internal algebraic inconsistencies in the
supplied final IEEE source, not an official publisher erratum. Physical channel
definitions determine the implemented correction. No curve fitting is used.

| Final equation | Diagnosis and retained physical identity | Exact small counterexample |
| --- | --- | --- |
| Eq12, p284 | Amplitude coefficients require squares in `E[gg^H] = beta^2 I + alpha^2 gbar gbar^H`. | Scalar alpha2, beta3, gbar1 gives13; the printed expression gives5. |
| Eq30d, p287 | For `w=sqrt(p) E[h]`, transmit power uses `p ||E[h]||^2`, as in the physical Eq25c; the self-interference fourth-moment coefficient is different. | Mean1, variance1, p3/4 yields physical power3/4 versus printed3/2. |
| Eq11c, p284 | Direct and cascaded complex means require the full absolute square and its phase-dependent cross term. | Unit scalar amplitudes and phases+1/−1 give8/4 including variance4; the printed form gives6/6. |
| Eq45c, p290 | The direct-only CN fourth moment has cross coefficient `2(N+1) v ||m||^2`. | N1, mean1 and variance1 give7; the printed direct-only limit gives5. |

The frozen full finite-Rician moments include cascaded NLoS products. The
implementation follows the stated physical channel model and original QT/RMO
structure with these explicit corrections. It does not claim literal agreement
with mutually inconsistent printed expressions or recovered author code.

## W versus I/N remains a separate source boundary

The final source's physical interference constraints and Fig11/12 W labels must
be distinguished from the existing bank's dimensionless interference/noise
threshold. With the bank's explicit−94dBm noise,
`I_W = 10^((-94-30)/10) * (I/N) = 3.9810717055349727e-13 * (I/N)`.
This resolves the bank's dimensional conversion. It does not recover the
author's executed normalization, despite the TableI dB threshold and plot W
labels. Existing normalized results must not simply be relabelled as W.
The fixed144-input bound in the retained unit proof also shows that literal
0.01W would be slack for those inputs; it is not evidence of author curve
agreement. No missing normalization is fitted or invented.

## Our earlier Algorithm3 implementation gap

The frozen legacy Python/native MR-S-TS and MR-TTS-TS omitted the final
Algorithm3 line2 pre-loop P9 followed by a single logical P7, and used a
reconstructed progress margin instead of the printed strict improvement test.
That was our implementation defect, not a paper error. Its old physical,
phase/QT and moment receipts remain as-executed; affected TS outcomes cannot
be upgraded to final-Algorithm3 conformance by relabelling.

The correction injects only the corrected Python `mr_two_stage` AST into the
original v3 installation and preserves the native thirteen-function science
suffix. It uses one complete existing P9 solve and one logical P7 with fresh
Eq32 auxiliaries, then the original full smoothing/final-power stages. Fresh
auxiliary initialization and the undefined Phi-star fallback to the post-
preamble phase are disclosed reconstruction choices, not recovered author code.
The old NoRIS power need not remain feasible after the phase changes. Preamble
acceptance retains finite/primal/QT/precision gates without assuming a feasible-
incumbent monotonicity theorem; ordinary same-phase full-loop guards remain.

Correcting this gap is not proof that it caused any author-reference difference.
Failure, caps, infeasibility, convergence, independent physics, source closure,
cross-language checks and original-reference agreement remain separate gates.
