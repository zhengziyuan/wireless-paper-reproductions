# Original-algorithm execution evidence — not full reproduction

This evidence belongs to `strict/`, not the superseded reduced previews under `papers/`.

The `components/` files are actual independent Python and MATLAB runtime outputs. Their shared-input comparisons check gradients, mathematical identities, original convex subproblems, objectives and physical residuals. Convex backends may return different nonunique optimizer vectors. The associated parity reports specify which sections and tolerances were compared. They do not claim every original figure or complete optimization chain has converged.

The current `figures/mis-sensing-fig2-python.png`, two render receipts and
`figures/mis-sensing-fig2-dual-parity.json` belong to the newly recovered original
EPS target-marker grid: azimuth0/45/90, elevation30/50/70 in elevation-major
order, full20x20/16x16 surfaces and91x361 angle samples per each of nine targets.
Actual independent MATLAB/Python full-grid outputs agree at the stated
tolerances; original-figure values do not yet agree and are not certified.
This is not a replacement for full RALM optimization.

Earlier ZIP archives, their parity report and nine older target PNGs are
preserved **historical diagnostics using the earlier, contradicted target
angle assumptions**, not the current source-marker figure. Their internal
dual-language agreement must not be presented as original-figure agreement.

The failed full-size sensing attempt is preserved as a diagnostic. Its eight completed starts did not produce a feasible converged result. It was stopped for debugging with the original 6000 / 30 / 4000 budget intact. Subsequent complete 30×4000 single-start diagnostics distinguish common-step and original per-block versions, feasibility, projected KKT residual, and outer stopping. They are not 6000-start figure results. No relaxed tolerance, substituted optimizer, partial batch or failed solve is counted as full reproduction.

Earlier per-block failures remain in `diagnostics/`. The newest original-marker
full-size single start is recorded in
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

`summary.json` binds the fresh six component outputs and comparisons to current
source hashes. MIS comparisons exercise the formal guarded per-block branch;
literal printed diagnostics are separate. `matlab-source-analysis.json` records
actual source diagnostics/version, not a complete numerical execution certificate.
All current figure images and historical diagnostic archives remain explicitly
distinct from certified original-paper figure reproductions.

Remaining analytical/source gaps and numerical convergence failures are listed in `../status.json`, package source contracts and READMEs. A green component workflow is never the full reproduction release gate.
