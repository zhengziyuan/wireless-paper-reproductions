# Communication cap-only control: distinct, not an original4000 certificate

The supplied final R2 TeX has SHA256
`6e27fb9fd2ba0decc9d7bcfc54bcb73612553f91f6df923ab502e7d561058cb0`.
Algorithm1 at source lines617–628 requires the inner Riemannian-gradient norm
to fall below an unspecified threshold and halves μ between stages. The active
convergence discussion at lines639–643 gives1000 as an example initial μ and
equally spaced alternative initial values, without supplying their range,
count, terminal μ, iteration cap, numerical gradient threshold, or start count.
Whole-file searches found no4000/6000/1e−6 values. The inherited implementation
therefore selected4000,6000 and1e−6; none is a quoted communication-paper value.
This differs from the sensing paper, which explicitly reports4000 inner steps.

This external version changes exactly one configuration field:
`rcg_max_iterations: 4000 -> 100000`. Initialization, full M4/N1/U4/K4 Fig8
scene, every original beam, μ chain, raw per-block PR, direction safeguards,
Armijo acceptance and the unchanged1e−6 implemented closed-simplex KKT stop
remain unchanged. Previously documented source-sign/domain errata remain
errata; increasing the cap does not make the implementation identical to the
printed open-simplex stopping condition, globally optimal, or original-curve
agreement certified.

Actual component evidence:

- All14 failures from one frozen partial old-bank snapshot were cold-run,
  without selecting survivors. All14 full μ chains passed, and every old
  history prefix through the first extended capped stage was bitwise equal.
  Maximum actual inner-record count was10840. This is not all12000 starts.
- Independent Decimal60 physical final-state checks passed for all14; maximum
  KKT9.994693073055577e−7, maximum difference from the recorded KKT
  3.032331364358296e−16 and maximum binary-SNR difference2.7755575615628914e−17.
- Fresh native MATLAB cold start66 ran both4000 and100000. A4000 cap was
  actually observed; all native original prefixes were identical through that
  stage. The extended chain passed all17 actual stops, independent scalar-loop
  physical gradients, domain and μ-chain checks, with runtime sources unchanged.
  A separate Decimal60 checker also passed all17 stage endpoints. MATLAB and
  Python trajectories are not claimed bitwise equal.
- The new executor's fresh MIS66 and SMS66 components both passed all full
  stages and independent gradients. Every applicable old Python prefix was
  bitwise equal. Its first SMS attempt exposed only a Decimal checker's
  empty-vector sum type error; that attempt and exact historical checker bytes
  were preserved, and the corrected checker was freshly tested on both banks.

The original4000 bank is not modified, re-labelled, or merged with these results.
The new external executor defaults to plan-only and requires the actual native
preflight and independent native Decimal receipt before any full execution.
The new bank must freshly execute6000 MIS+6000 SMS starts. All failures remain
visible; best-feasible selection and best-numerically-verified selection are
separate. The released full numerical-success gate requires all12000, not just
the selected best. No full bank has been launched by this component task.

Entry-point/renderer audit:

- `mis-communications/run.py` diagnostic/full guards and the MATLAB public
  header/diagnostic guard hardcode4000, as does the old root executor. These
  guarded entrypoints remain untouched.
- The external MATLAB bridge contains a new dispatch header followed by the
  original complete41,112-byte local-function suffix, byte-identical at runtime
  (SHA748dfdeb2674b0377abb1680103d3d436f1dbe886244f65c75ea8e55a7a5a89b).
  It is explicitly not a call through the original guarded entrypoint.
- The root plotter has no numerical4000 test; its scope whitelist does not
  recognize this new extended-control scope. The external versioned renderer
  validates all12000 actual records and source bindings before using only the
  unchanged plotting function. It retains the original-agreement warning and
  labels its receipt as an unreported-cap control. No partial-bank plot is
  accepted as a full figure.

This evidence supports a disclosed numerical-control release path, not a
published100000-budget claim or a convergence guarantee for every start.
