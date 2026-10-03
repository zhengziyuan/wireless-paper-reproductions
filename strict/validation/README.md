# Original-algorithm execution evidence — not full reproduction

This evidence belongs to `strict/`, not the superseded reduced previews under `papers/`.

The `components/` files are actual independent Python and MATLAB runtime outputs. Their shared-input comparisons check gradients, mathematical identities, original convex subproblems, objectives and physical residuals. Convex backends may return different nonunique optimizer vectors. The associated parity reports specify which sections and tolerances were compared. They do not claim every original figure or complete optimization chain has converged.

The current same-reference correctness evidence is isolated in
[`sensing-correctness-v2/`](sensing-correctness-v2/). Fresh independent
MATLAB/Python closed-form runs retain20×20/16×16 surfaces, all nine original
target markers and91×361 angular samples for every target. Their full-grid
comparison passed at1e−9 tolerance, and the new PNG layout is rendered from
those actual numerical samples. Both phase vectors use a shared reference and
are conjugated consistently with the positive array exponent; source-law
placements are not replaced by a best-SINR search. This verifies the corrected
finite-field implementation, **not agreement with the original Figure2** or a
full RALM bank.

`figures/mis-sensing-fig2-python.png`, its older two render receipts and
`figures/mis-sensing-fig2-dual-parity.json` are now **historical, superseded**:
they use the earlier inferred MS2-only maximum-span phase-origin offset.
Although their original target-marker grid is recovered correctly, their
phase convention is not the new same-reference construction. They remain
preserved with their original identities and must not be cited as current
correctness evidence.

Earlier ZIP archives, their parity report and nine older target PNGs are also
preserved historical diagnostics. They include the contradicted earlier angle
assumptions and pre-correction MS2-only phase-offset convention, not the
current same-reference result. Their internal dual-language agreement must
not be presented as current-model or original-figure agreement. No old archive
or image is overwritten to disguise the change.

The new correctness set also records the eleven-case independent Decimal
reference check of the exact SINR/ALM increment in both Python and MATLAB, and
the six normalization tests including overflow rejection. Those identities
verify the numerical formulation; they are not full-paper optimiser sweeps.

The explicit effective-reference factor100 candidate was rerun in both
languages against all six original continuous-RIS power points with full
M100/four-target scenes and original per-start budgets. The continuous curve's
maximum error is0.00835384dB; 1bit and2bit errors are1.1727642dB and0.3385719dB.
These are actual simulation/reference comparisons, not original points copied
into a renderer. There is one deterministic initialization per target/power,
**not6000 starts**, and neither language verifies every inner/outer stopping
criterion. MATLAB's epigraph feasibility tests pass; Python's27dBm target3
epigraph residual1.000308913e−6 exceeds the unchanged1e−6 limit and is recorded
as failed, although its evaluated physical phase-domain curve remains valid.
The tolerance is not relaxed to make that flag pass. This supports an effective
reference/noise fingerprint, not a proven Tp100 or an all-original-figure
reproduction certificate.

The failed full-size sensing attempt is preserved as a diagnostic. Its eight completed starts did not produce a feasible converged result. It was stopped for debugging with the original 6000 / 30 / 4000 budget intact. Subsequent complete 30×4000 single-start diagnostics distinguish common-step and original per-block versions, feasibility, projected KKT residual, and outer stopping. They are not 6000-start figure results. No relaxed tolerance, substituted optimizer, partial batch or failed solve is counted as full reproduction.

Earlier per-block failures remain in `diagnostics/`. The historical original-marker
full-size single start, before the stable-increment correction, is recorded in
`../mis-sensing/diagnostics/fig3-recovered-grid-full-start-receipt.json`:
418.97s,30 outer iterations and20274 actual inner iterations with unchanged4000
per-call caps. Minimum binary SINR49.53525 and maxq7.2813e-8 are feasible, but
final projected/KKT2.6004e-5 exceeds the active1.2589e-6 threshold.16 inner
tolerance exits,2 caps and12 line-search failures are retained. Zero failed-step
length does not certify convergence. Neither it nor the earlier689.24s/v2
failure represents a6000-start bank. Old checkpoints cannot be reused with
changed sources.

The first ISAC500-cap failure and isolated2828-iteration trial remain preserved.
The complete six-scheme rerun with the disclosed10000 cap took907.67s and passed
all recorded original inner/outer stopping and physical checks; see
`../rotatable-isac/diagnostics/2026-10-03-case0-w10000.json`. It binds an immutable
input/configuration snapshot, not a current-config reusable bank. This does not
prove all-block nonconvex stationarity, a RIS gain in its zero-bridge realization,
or a complete100-channel point/figure.

Satellite bounded-chain outputs explicitly retain capped/not-converged algorithm statuses and primal/QT/SDR residuals. Their physical constraints passed within recorded tolerances, but their complete production sweeps have not been validated. The current formal Hotspot method is RGD/QT.

`summary.json` binds its six component outputs and comparisons to the source
hashes recorded in that receipt. Changed implementations require a fresh
receipt; an older summary cannot certify later edits. MIS comparisons exercise
the formal guarded per-block branch;
literal printed diagnostics are separate. `matlab-source-analysis.json` records
actual source diagnostics/version, not a complete numerical execution certificate.
All current figure images and historical diagnostic archives remain explicitly
distinct from certified original-paper figure reproductions.

Remaining analytical/source gaps and numerical convergence failures are listed in `../status.json`, package source contracts and READMEs. A green component workflow is never the full reproduction release gate.
