# Original-model controls and evidence boundaries

The source contract is the supplied author manuscript and thesis equations
4-5, 4-9 through 4-46, and Algorithms 4-1 through 4-3. Publisher-version and
historical curve conformance remain unverified. The eight original AP/MR,
statistical/TTS, NoRIS/PA/TS schemes retain full finite-Rician covariance and
shared ground fading across satellites, all power/leakage constraints, the
original quadratic transform, and the full squared residual penalty. The
penalty is not changed to a hinge, and no power share is fixed.

## Exact derivative contraction

For one selected RIS coordinate set, let `D_m = i phi_m G_m mean(r_m)`.
The full second moment has the original derivative
`dQ_m = D_m mean(h)^H + mean(h) D_m^H`; its covariance is phase independent.
Consequently `tr(B dQ_m) = 2 Re(mean(h)^H B D_m)` for Hermitian B. Computing
these columns together avoids repeatedly multiplying zero matrices. The
retained scalar-coordinate oracle, the production contraction and all 50
coordinate finite differences are checked independently in
`verify_phase_derivatives.py`, at both finite-Rician factors 0 and 20dB.
The MATLAB counterpart independently evaluates the same shared fixture.

## RGD numerical controls, not a theory change

RGD is explicitly allowed by the source. The ascent direction for maximizing
the source objective is equivalently the negative gradient of its negative;
the source's isolated negative-gradient prose cannot be used to minimize a
quantity declared as a maximization objective. The same circle retraction and
Armijo sufficient-increase constant `1e-4` are retained. The unreported
positive initial step is the inverse original gradient norm; later positive
Barzilai--Borwein curvature estimates seed the same original halving search.
With angular step s and ascent gradients g, `alpha=||s||²/[s^T(g_old-g_new)]`
is used only when its denominator is positive, otherwise twice the prior
accepted step seeds the search. This chooses a scalar step, never a different
direction. AP solves each RIS independently, as Algorithm 4-1 states; a row
already below the stricter `tol/sqrt(U)` bound is held fixed while other rows
proceed. A zero row step is exactly the identity, not another floating-point
renormalization that could introduce a false decline.

An earlier implementation had a tiny-progress exception accepting ten times
the configured gradient tolerance. That was an implementation defect, not a
paper theorem, and is removed in both languages. The real joint `1e-6`
gradient test is required; capped blocks are recorded as failures. No failed
or capped scenario point is discarded or promoted to a figure certificate.

The original scalar/alpha-one full base run actually exhausted the smoothing
repeat cap after 2137.44s. That receipt remains a failed diagnostic, never a
successful result for the new controls. Numerical controls and derivative
equivalence alone do not certify full-sweep convergence or original-curve
agreement. The later unit-initial-step 500-cap full-size run still exhausted
50 smoothing repeats after 460.27s; the unreported safety cap is therefore
increased to 5000 without changing the `1e-6` gradient stopping threshold.
Actual results bind source hashes, configurations and checkpoint
contracts before any selected sweep is accepted for rendering.

## Exact stable objective increments

The positive-BB 5000-cap AP run encountered a numerical Armijo failure at
joint gradient `1.117476e-6`, just above the unchanged `1e-6` threshold.
Subtracting two objective values near 24 produced a spurious `-4.97e-14`
decline. That failed receipt is preserved. No roundoff allowance is added
to the Armijo inequality and no gradient tolerance is relaxed.

For an amplitude x and exact change dx, use
`delta|x|²=2 Re(conj(x) dx)+|dx|²`. For a SINR `a/b`, the exact increment is
`(delta(a)*b-a*delta(b))/(b*(b+delta(b)))`. All original finite-Rician
covariances are phase independent on the unit circle. MR-S cross moments
are `m_i^H C_u m_i+|m_u^H m_i|²`; MR-TTS cross moments are
`tr(Q_u Q_i)` for different users and the full conditional-Gaussian fourth
moment for the same user. Expanding these polynomials gives exact changes
without subtracting two nearly equal large objectives.

For the original smooth minimum, let weights be its current soft-min
weights and ds the SINR changes. Its exact change is
`-mu*log(sum_u weights_u*exp(-ds_u/mu))`. Near stationarity `log1p/expm1`
evaluate this same identity stably; large trial steps use centered
logsumexp. The original residual penalty has exact change
`2 residual*deltaLeak + deltaLeak²`. MATLAB implements the same identities.
`verify_increments.py` and `strict_satcom_increment_test.m` independently
compare full-dimensional values at both finite Rician factors and at
large-to-near-zero phase perturbations. The zero step is exactly zero.

## Same-input QT numerical guards

An original full-dimensional sweep exposed numerical backend failure at
2.828427W and 11.313708W, and an independently rejected QT bound at 8W. Old
receipts and every unsuccessful attempted solve are preserved. The preferred
entry does not replace QT or discard these scenarios. For an immutable current
iterate it invokes the original AP/MR QT with exactly the same coefficients,
auxiliaries, physical constraints and objective. Only conic-solver numerical
precision, regularization, equilibration and numerical iteration controls may
change; the mathematical subproblem is unchanged. If no attempt independently
passes, the original block is still an explicit failure.

Every returned attempt must have finite residuals, original normalized primal
violation at most `1e-5`, QT upper-bound violation at most `1e-5`, and original
minimum-SINR decrease no greater than its existing `1e-5` numerical gate.
Acceptance never follows from a backend status alone. Independently generated
same-input fixtures bind their numeric arrays by SHA256 and are not author
manuscripts or recovered original code.

Actual MR-TTS-NoRIS at 2.828427W failed with the original backend controls and
again at `1e-9`; `1e-10` with `1e-12` static regularization solved the same
block, with primal and QT violations zero and minimum SINR increasing from
0.25498162307 to 0.2604130083. A second MR-TTS-PA input had original QT bound
violation `1.605923e-5` and was rejected. The same input at `1e-9` returned
`4.191556e-6` bound violation and `1.1318e-7` primal violation, both below the
unchanged gates. These are numerical fingerprints, not historical curve fits.

`qt_numerical_guard.py` performs these same-problem retries. MATLAB's isolated
`strict_satcom_qt_guard.m` retains the same independent acceptance gates while
trying stricter CVX precision and restoring the caller's original precision.
`strict_satcom_qt_guard_test.m` independently solves the generated numeric
fixtures. Python mock-based contract tests separately verify no mutation and
no silent relaxation; they are not numerical solver evidence.

A fresh full guarded 8W scenario actually completed all eight original chains,
all original stopping tests, all four gates and 1000 independent finite-Rician
moment draws in 84.82s, with unchanged runtime source hashes. The complete
guarded figure bank is a separate fresh execution, never a mixture of earlier
unguarded successful and failed points. Publisher-version agreement and
historical-curve conformance remain uncertified until separately checked.

## Preserved M30 full-bank failure: exact-polynomial increments are not closure

The fresh guarded full sweep preserved a genuine M30/LEO-Rician20 failure in
MR-S two-stage RGD: after141 iterations its gradient2.258355e−6 was above the
unchanged1e−6 stop, and the original Armijo search exhausted. This point is
explicitly invalid, regardless of earlier completed schemes. A new independent
same-full-scene diagnostic reproduced the failure in16.85s and bound its saved
numeric input fixture by SHA256; see `diagnose_rgd_search.py` and
`outputs/M30-RGD-Armijo-diagnosis.json`. No current production source changed.

At its first trial alpha0.000623304, a tangent displacement of1.40764e−9 gives
first-order increase3.17895e−15, while its existing polynomial increment
evaluates−6.61881e−15. The algebraically equivalent angular circle retraction
gives a positive1.37013e−15 with otherwise identical input. Some separately
declared initial-step resets pass the same original Armijo test, but this is
diagnostic evidence only: neither a reset nor high-precision proof is a new
completed production chain yet. The failed point is not relabelled, the
gradient/Armijo threshold is not relaxed, and a whole-sweep pass is not claimed.
Numerical representation of the near-stationary circle step remains under
independent audit; previous exact-increment component checks do not certify
this newly exposed case.
