# MA Figure 6: completed 900-case saved mathematics and full-population language comparison

The independent native saved-state reader has completed all **900 of 900**
configured cases with all four mathematical stages passing. The current
aggregation retains **three intermediate-trajectory comparison exceptions**:
897 cases have matching paths under the original fixed comparison gates;
all 900 have terminal sample rates within 1e-7 bit/s/Hz and independent
own-state means within 1e-9 bit/s/Hz. Original-reference agreement remains
unverified and the existing unfitted curves differ materially from the source.

This updates the execution status of the earlier
[complete first-case mathematical witness](../MA6-saved900-first-complete-math-witness-20261017/README.md).
It does not replace the [complete return aggregation](../MA6-native900-execution-closure-20261017/README.md)
or the [original R2 reference comparison and plots](../MA6-closed900-original-reference-20261017/README.md).
Those closed results are reused without new optimization or random draws.

## Population and completed checks

The population is every power in 9:3:33 dBm, with 100 configured geometries
per power and 1000 NLoS draws per geometry, N=6, M=5, kappa=6 and A=2.
The 100/1000 counts, random inputs and numerical caps are the disclosed
reconstruction configuration; the author's original Monte Carlo counts,
seed and initial geometry have not been recovered. No failed case is dropped.

| Check on the actual saved cases | Coverage |
| --- | ---: |
| Full saved-state physics and geometric constraints | 900/900 pass |
| Original ordered MA histories and stopping conditions | 900/900 pass |
| Five terminal schemes, each with all 1000 sample rates | 900/900 pass |
| Original coordinate minorants and fixed coordinate gap constraints | 900/900 pass |
| Same intermediate path under the existing 1e-9 position/objective gates | 897/900 pass |
| Saved terminal sample-rate differences below 1e-7 | 900/900 pass |
| Independent own-state mean differences below 1e-9 | 900/900 pass |

Native fixed-array results are checked against already closed independent
Python scalar/batched references on byte-identical job/config inputs and
matching evaluator sources. This reuses complete 1000-draw verification; it
does not recover the original fixed-array per-iteration W/QT/KKT records.
The two hardcoded `difference=false` fields in the original comparison helper
are excluded from the evidence gates.

The maximum terminal sample difference is 1.0011692808120642e-8 bit/s/Hz
(MA-ZF). The maximum independent own-state mean difference is
4.854534552123368e-10 bit/s/Hz (MA-ZF). The maximum residual after subtracting
the independently evaluated own-state difference is 3.169793316715186e-10
bit/s/Hz (FPA-ZF). The supplementary 2e-7 residual bound is the sum of the
two existing 1e-7 evaluator error bounds, not a published-paper tolerance.

## Retained intermediate-path exceptions

The indices below are the original zero-based saved history indices. All
three histories have equal Python/MATLAB lengths; all three terminal position
and design-objective differences are below 1e-9. The intermediate failures
remain failures of the original comparison gate.

| Case | Mode | History length | First differing index | Maximum prefix position difference | Maximum prefix objective difference |
| --- | --- | ---: | ---: | ---: | ---: |
| 27 dBm, geometry 24 | MRT | 74 | 50 | 1.4391680069891777e-9 | 1.4624076172253808e-8 |
| 27 dBm, geometry 27 | ZF | 485 | 345 | 3.467051090666473e-10 | 1.174324637531754e-9 |
| 33 dBm, geometry 24 | MRT | 73 | 58 | 1.506084e-10 | 1.600345e-9 |

The exact unrounded values and every other scheme comparison are retained in
the payload. This evidence does not establish a cause for these deviations,
bitwise equality, global MA optimality, or identical complete trajectories.

## Public payload and replay boundary

`all900-scientific-summaries.json.gz` contains the actual per-case mathematical
gates and full comparison fields for all 900 cases, with original input,
RAW and scientific-receipt identities. It also retains the SHA256 of each
complete local summary. Local host paths and runtime descriptions are omitted
from this selected-field transport. The full local numerical archives remain
preserved; they are not all embedded in this compact packet.

`actual-population-closure.json` records the completed population and actual
child exit code 0 with unchanged sources. A historical `available=false`
template field and stale `running` progress label were not rewritten; neither
overrides the explicit completed terminal summary.

Run this command with a fresh output path:

```text
python strict/validation/ma6-all900-saved-science-20261020-v1/replay_summary.py --output new-ma6-summary-replay.json
```

The standard-library reader checks every delivered case, rederives the path
and sample gates from numeric summary fields, recomputes all maxima and
retains the three exceptions. This command replays **summary aggregation**;
it does not rerun the 900-case underlying physics. The prior full first-case
witness and `tools/ma-saved-replay` provide the numerical reader and one
complete portable input/state archive. A successful summary replay is not a
new scientific experiment.

## Original source and remaining limits

The existing no-fit comparison with the supplied author-R2 `P_6_4.eps` still
has all 45 point gaps per language above one EPS ordinate rounding step.
The maximum absolute gaps are 2.4759 (MA-ZF), 1.4737 (MA-MRT), 2.0840
(FPA-ZF), 0.8047 (FPA-MRT), and 1.2657 (FPA-OPT) bit/s/Hz. Vector rounding
is not a statistical acceptance threshold for the unknown author ensemble.
The R2 prose/figure ordering qualification is documented in that reference
packet; final-publisher equivalence is not asserted.

Missing author inputs, historical producer-time receipts for the old 759
recovered Python files, historical FPA step states, exact-real interval
certification and original-reference agreement remain distinct limitations.
The three path exceptions also remain open. This packet does not claim full
paper or six-paper completion.
