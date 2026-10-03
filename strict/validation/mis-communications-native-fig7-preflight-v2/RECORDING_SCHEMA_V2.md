# Isolated native Fig7 recording source v2

This source version retains v1 unchanged, including its actual false preflight
receipt. In that receipt all four numerical/reference and saved-history checks
passed, as did source before/after identity and original stopping gates; only a
metadata assertion incorrectly required the JSON-decoded `ms1` to be a row.
The fresh external checker-v3 tests `numel(ms1)==2` and `ms1(:)==[1;2]` only for
that two-element metadata, retaining exact original configuration byte comparison.
It does not reshape or squeeze any state, history, matrix or stop array.

## Additional initial observation fields

The three observation sites and all numerical updates are unchanged. At the
initial site only, v2 additionally saves already-computed native model data:

- `initial.actual_steering_matrix.real` and `.imag`: actual MATLAB `model.c`,
  with shape 4-by-2 for both Fig7 schemes. No cross-language reconstruction.
- `initial.actual_indices_one_based`: actual `model.indices`, shape 2-by-1
  for MIS, 1-by-0 for SMS. Index origin is explicitly MATLAB one-based.
- `initial.actual_model_dimensions`: scalar `M`, `N`, `U`, `K`, `targets`.
  MIS is `(2,1,2,4,4)` and SMS `(2,0,1,4,4)`; these dimensions preserve the
  meaning of the SMS empty index array in JSON readers.

The rest of the v7 scalar `payload` is as in v1: each actual mu endpoint in a
1-by-J `continuation_stages` cell, its own state/complete inner h/raw PR/stop,
the original `full_history`, and final state/metrics/solver status. No inner
iterate state is fabricated; `every_inner_iterate_state_saved=false`.
Independent physical KKT and original-curve closeness remain false until their
separate actual audits. The stored C allows the independent evaluator to check
both geometry reconstruction and the physical quantities of the actual binary
native steering values separately.

The new exact inverse proof returns the same original engine bytes/hash after
removing observation/version metadata/dispatch and restoring the two old growing
checkpoint I/O arguments. Original paper-package files remain unchanged. The
1x2 Fig7 geometry is the explicit `COMM-GEOMETRY-FIG7` correction, not a claim
to have recovered the printed 2x1 historical setup. The 6000 starts per scheme,
4000 RCG cap and 1e-6 threshold are retained reconstruction controls, not numeric
values reported by the communication article.

## Runtime entry points

The frozen source is `scientific-source/`. The external checker
`run_recording_two_start_preflight_v3(freshFolder)` cold-runs the fixed original
MIS1 and SMS1 full starts plus unchanged numerical references, verifies all
numerical fields byte-exactly, and additionally compares saved C/indices/dimensions.
The unexecuted earlier two/four-start source plans are preserved, not retrofitted.
Actual execution receipts, not these plans, determine runtime success.

`run_recording_full_fig7_checked_v2(freshBankFolder)` is a separate source/runtime
binding wrapper. It cold-runs all 6000 MIS + 6000 SMS starts, retains every
actual mu endpoint (expected 230400), preserves false original stop flags, and
stores before/after source/runtime identity and all record hashes. Immutable
per-start v7/JSON files and numbered progress retain partial evidence if I/O or
execution interrupts. No old preflight output counts as a bank result, and no
failed partial attempt is silently resumed or overwritten. This full entry
requires one MATLAB computational thread. The new bank is distinct v2.
