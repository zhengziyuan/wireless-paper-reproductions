# ISAC014 native remaining five: closed returned states and retained failures

This capsule covers only native schemes 2–6 at the same case014 scene/configuration. Scheme1 is already published in [the sibling native first-scheme capsule](../native-returned-states/README.md) and is not rerun or duplicated here. The original native producer naturally returned **2**, retaining the scheme3 and scheme5 algorithm failures. Its actual held/source closure is included. The independent saved-state MP80/MP100 reader naturally returned **0**, with its own exact held identity, source/input closure and no host errors. Reader0 does not turn the producer2 or failed strict stops into success.

The completed evidence contains **84 internal returned states plus five final states = 89 states**, at both precisions. Schemes2/3 exactly reuse their already completed 42 internal + two final states and report digests; V2 computes only schemes4–6 (42 internal + three final). No optimizer, channel generation, MC, random draw or new line-search trial was executed for this package.

| Ord | Scheme | Producer exit | AO blocks | Internal + final | Physics/feasibility/formula | Own strict RCG/PGA | Final RCG / PGA |
|---|---|---:|---:|---:|---|---|---|
| 2 | Rot-BS & Fix-RIS | 0 | 2 | 6 + 1 | PASS | PASS | PASS / PASS |
| 3 | Fix-BS & Rot-RIS | 2 | 12 | 36 + 1 | PASS | FAIL | FAIL / FAIL |
| 4 | Fix-BS & Fix-RIS | 0 | 2 | 6 + 1 | PASS | PASS | PASS / PASS |
| 5 | Rot-BS & No-RIS | 2 | 15 | 30 + 1 | PASS | FAIL | N/A / FAIL |
| 6 | Fix-BS & No-RIS | 0 | 3 | 6 + 1 | PASS | PASS | N/A / PASS |

“Own strict” concerns applicable returned RCG/PGA endpoints, independently checked against their own fixed inputs. Scheme3 fails RCG block6; scheme5 fails PGA blocks1/2. At the final coupled state, scheme3 fails both RCG/PGA norms and scheme5 fails PGA. Full exact MP decimal residuals remain in `SCOPE.json` and the complete reports. NoRIS schemes5/6 have W/PGA returns only: RCG is **not applicable**, never an invented passing state. Fixed RIS orientation still permits the actual RIS-phase RCG updates in schemes2/4.

W used the recorded MM/relative-stop rule. Its absolute stationarity was not an author-specified pass gate; the power-ball ray multiplier is a diagnostic estimate, not a proved KKT multiplier. All five W residuals/complementarity diagnostics are preserved. Passing physics and the corresponding derivative formula, or passing a block's own strict criterion, does not prove final joint stationarity. Original-reference, independently optimized dual-language equality, full-six convergence and full-paper gates are not promoted.

The V1 saved reader naturally returned1 after schemes2/3 had completed because MATLAB encoded an actual one-element scalar history as a number: `TypeError: object of type 'float' has no len()`. V2 normalizes only those status containers whose recorded count requires one value, verifies the value's IEEE bits, and precisely adopts the two completed reports. Its per-scheme MP mathematical source remains whole-byte identical. V1 failure and the exact source inverse are included; no old state was reoptimized or re-audited for convenience.

Each `saved/scheme-*-original-native.mat.gz` decompresses to the exact authoritative closed MAT bytes and original SHA; no MAT dtype, shape, complex value or signed zero was rewritten. Complete MP reports are lossless gzip after metadata-path-only projection. The combined saved fixtures contain actual state arrays plus **new common Python binary64 evaluations at those native arrays**. Those comparisons are not captured native analytic vectors. The first-scheme's separately published 36-vector check applies only to that first scheme. The new remaining-five direct-native vector task is outside this capsule's completed scope.

The data/source/configuration and all independent decimal outputs retain original numerical tokens, scalar types and float bits; only machine-path metadata is replaced by stable logical aliases. `TRANSPORT_PRESERVATION.json` records the original/projected/compressed hashes. Shared independent physics/derivative sources, original native QP/stable-increment source and first schema helper are referenced with exact relative filenames/SHA in `SOURCE_PROVENANCE.json`, avoiding duplicate parent data/reference files. Newly executed multi-scheme sources are included whole-byte for provenance. Their original private routing is retained in those original source bytes; this package introduces no new public mathematical runner or claimed portable MP first-use.

The complete original 28-control configuration and original scene are included. AO500/W10000/RCG5000/PGA5000, gradient1e-6, PGA relative1e-10 and 80-trial Armijo controls are disclosed reconstruction/variant controls, **not claimed recovered author numerical budgets**. This is case014 evidence, not a full population, historical in-memory-vector recovery, proof of paper formula error, or an original-author reference match.
