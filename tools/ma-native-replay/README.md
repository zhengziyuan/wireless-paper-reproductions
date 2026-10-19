# Original full900 native MA6 execution

This recorder calls the existing `run_full_ma_figure_v2` exactly once over
the complete Fig6 bank. It does not edit, transform or replace the numerical
kernel. All900 shared original inputs, five schemes,1000 NLoS draws per
geometry, original9:3:33dBm grid, N6/M5/kappa6/A2, disclosed AO10000/FPA1500
caps and5e-5 fractional stop remain. The recorded scopes and fresh output
parent differ from the older Figure5 metadata recorder; its entire source
and the reversible scope-edit proof are retained.

Prepare metadata over an existing complete immutable exported bank:

```powershell
python -B tools/ma-native-replay/prepare_plan.py --bank E:/saved/MA6-bank --plan E:/new/MA6-native-plan.json --output-parent E:/new
```

The command prints the exact plan SHA256. It validates every original job
fingerprint and numerical control and does not start MATLAB. In a fresh
MATLAB session with this directory and `strict/two-timescale-ma` on its path,
use `run_owned_native_MA6_900(plan_path, exact_printed_SHA256, fresh_output)`.
The output must be a new direct child of the declared data directory. Use
the repository's session-local runtime activation and a separate preference
directory; no persistent MATLAB path or network setting is changed.

The recorder checks actual selected source resolutions and byte hashes,
all900 input hashes, metadata and selected MATLAB/runtime identity before
and after the original call. Each actual RAW output is linked by exact
path, source-input identity and hash. The original entry writes progress
only after a case has returned. Recorded schema/counter/source gates are
separate from the independent physical reader and original-reference checks.
Every original failure is retained. Parent exit, complete file count or a
positive stored flag alone is not independent scientific certification.

The native900 has now completed with unchanged numerical kernels and inputs
and a verified actual parent closure. All4.5million terminal-rate returns were
compared with the existing saved Python900 composition. Its complete data and
limits are in the [closed900 packet](../../strict/validation/MA6-native900-execution-closure-20261017/README.md).
The first native RAW has passed
the independent paired reader in the [public first-case witness](../../strict/validation/MA6-saved900-first-complete-math-witness-20261017/README.md).
The full900 independent mathematical readers, original-author input recovery
and full-paper validation remain open. The public compact closure reader
checks4500 aggregate rows; it does not recheck the externally preserved RAW.

The [complete Fig6 original-reference comparison](../../strict/validation/MA6-closed900-original-reference-20261017/README.md)
now pairs all45 stored curve points per language with the actual R2 source
vectors and recomputes geometry SD/SE from all4500 public aggregate rows.
`compare_closed_curve_reference.py` optionally revalidates the original private
EPS; `replay_reference_evidence.py` verifies both public packets and repeats
all source/mean/variability/ranking calculations. Maximum source gap2.4759
bit/s/Hz and the R2 prose/12dBm ranking qualification remain visible; no
gain fitting, original-ensemble recovery or full900 mathematical pass is claimed.
