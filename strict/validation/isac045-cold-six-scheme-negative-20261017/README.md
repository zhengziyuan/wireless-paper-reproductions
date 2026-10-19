# Completed ISAC045 cold six-scheme control: convergence remains negative

The actual cold stable-arithmetic control returned normally after15,279.515s
on2026-10-17. Five schemes saved terminal states; `Rot-BS & Rot-RIS` reported
an RCG Armijo failure and saved neither its failure state nor its trial tape.
Only `Fix-BS & No-RIS` passed the complete configured convergence checks.
This is one full-size scenario, not a500-realization or full-figure result.

The control reads the unchanged strict source into an isolated module. It
uses explicit self-excluded interference sums in the metric and QT auxiliary,
and retains the actual original scenario, initialization and configured
W10000/RCG500/PGA500/AO500 limits. The frozen configuration also retains the
documented non-ascent RCG restart and PGA ascent-sign BB interpretation.
These interpretations and reconstructed controls are not recovered author
code or proof of literal printed-algorithm conformance. No tolerance or cap
was changed to obtain a passing result.

| Scheme | Saved AO steps | Configured complete convergence | Outcome |
| --- | ---: | --- | --- |
| Rot-BS & Rot-RIS | Unavailable | Failed | Armijo failure; no saved terminal state or trial vectors |
| Rot-BS & Fix-RIS |500/500|False|Outer budget exhausted;499 RIS block caps |
| Fix-BS & Rot-RIS |500/500|False|Outer budget exhausted;500 RIS block caps |
| Fix-BS & Fix-RIS |500/500|False|Outer budget exhausted;500 RIS block caps |
| Rot-BS & No-RIS |500/500|False|Outer budget exhausted |
| Fix-BS & No-RIS |5/500|True|Original relative-objective stop; all applicable inner stops |

The independent actual-history reader checks every one of2005 saved AO
decisions and6015 block scalar decisions, including all stored QCQP scalar
records in the external full history. All decisions are consistent with the
original configured thresholds;1499 RIS and27 rotation block caps remain.
Stored QCQP residual/power fields are not an independent historical QCQP
matrix/KKT certificate.

All five returned W/theta/rotation states pass independent MP80/MP100 full
channel, self-excluded SINR, rate, sensing pattern, NMSE, utility and feasibility
checks. All five W/RIS/rotation gradient comparisons pass the existing1e-5
component bound. Rotation references use a1e-20 central difference, while
W/RIS use independent analytic derivatives; no interval certificate is claimed.

At the last saved fixed PGA iota, the three active rotation schemes have
independently recomputed projected-gradient norms0.0155681803554393,
0.000735193930712367 and0.0000979450269846185, respectively. Each last PGA
call stopped on its configured relative-step criterion, while its norm remains
above1e-6. The step criterion is retained as a valid configured stop; it does
not certify that gradient threshold. Returned after-PGA RIS gradients also do
not recreate the preceding RIS block's fixed-rotation state.

`manifest.json` binds nine actual payloads: the full-history audit, terminal
gradient audit, all6015 compact block contexts, all2005 AO objective contexts,
five actual state witnesses, minimal gradient replay input, original config,
original scenario and independently observed parent return. The exact
190,303,353-byte original result remains external under its SHA256. This
packet includes every returned scheme and preserves the sixth scheme's
failure. The unavailable failed trajectory cannot be inferred from the other
five states or the earlier subtractive-arithmetic failure packet.

With `strict/requirements.txt` and `mpmath==1.4.1`, use a fresh destination:

```text
python tools/isac-line-search-replay/replay_cold_control.py --packet strict/validation/isac045-cold-six-scheme-negative-20261017 --output-dir new-cold-control-replay
```

The public command verifies all nine payload hashes, all included AO/block
scalar decisions, and freshly recomputes all five physical and terminal
gradient states. It does not re-read the absent190MB histories, recompute
their historical QCQP matrices, rerun optimization, reconstruct the failed
scheme, or establish MATLAB, original-figure or full-paper agreement.
