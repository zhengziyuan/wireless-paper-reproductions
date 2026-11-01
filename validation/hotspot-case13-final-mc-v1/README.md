# Case 13: saved Monte Carlo vectors and arithmetic audit

This is a retained **single-case observation**, not a full paper reproduction.
It concerns U=1, satellite Rician factor 20 dB and the saved statistical
designs labeled `NoRIS`, `TwoStage`, and `AO`.

The retained projection has 1000 finite recorded HU rate samples per scheme.
An arithmetic audit, rerun on those vectors, obtains the following:

| Saved scheme | Recomputed mean | Recomputed sample standard error |
| --- | ---: | ---: |
| NoRIS | 4.731317681185383 | 0.003299196996970837 |
| TwoStage | 10.570597459522535 | 0.0022755096768288926 |
| AO | 10.570596972343877 | 0.002275591701168829 |

The largest difference from a saved mean is approximately `1.78e-15`; the
largest difference from a saved standard error is approximately `4.34e-19`.
The standard error uses the sample standard deviation with `n-1`, divided
by `sqrt(n)`. There is no rounding-based alteration of the saved values.

For each scheme, the projection records the prescribed starts 0 and 1 as
executed; its selected IDs are respectively 1, 0, and 0. The producer records
all four per-start checks and convergence/algorithm-success flags as true.
Those are **reported flags**, not independent proofs of the underlying
constraints, stops, or selection optimality. See `recorded-audit.json` for
the recorded fields, consistency checks, and precise arithmetic differences.

The input is the lossless gzip `recorded-projection.jsonl.gz`, created from
the one 59,899-byte projection output of a guarded, identity-locked, bounded
read. The reader retained no original path or exception text. The worker read
two fields totaling 206,295 bytes from the earlier case index, not a full new
optimization. Its sanitized child and guard receipts are supplied separately.
The recorded index and file identity do not authenticate historical bytes or
prove an atomic whole-event snapshot. Guard success proves neither scientific
acceptance nor a hard filesystem quota.

The original command producing the arithmetic audit did not pin the audit
source bytes in advance. Replaying the published current source can reproduce
the report on this arithmetic runtime, but does not authenticate those earlier
executed bytes. Exact floating output may differ across runtimes.

Neither a saved sample count nor the producer's name `independent_MC` proves
the historical channel draws were independent, paired as intended, or matched
the authors' original random stream. The extracted projection does not bind
the author source code, recover original coordinates, verify the full paper
constraints or figures, establish MATLAB/Python parity, or independently
verify physical feasibility and convergence. It also does not independently
recompute the ratio-of-empirical-powers rate. No paper-level PASS is claimed.

The record-only replay inflates the gzip into bounded memory, invokes the
published audit on that record and compares its JSON to `recorded-audit.json`.
It does not read the old trajectory, create a decompressed file, or rerun any
science. From a complete checkout of the branch:

```text
python -I -S -B validation/hotspot-case13-final-mc-v1/verify_report.py
python -I -S -B tools/hotspot-case13-final-mc-audit-v1/test_audit_recorded_mc.py
```
